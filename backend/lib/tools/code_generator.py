import json
import re
import os
from ..llm import call_llm

class CodeGeneratorTool:
    """
    Tool for generating Python engineering scripts.
    Used by Engineering Core Executor.
    """
    
    def __init__(self):
        # Path logic: lib/tools/../../prompts
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.prompt_path = os.path.join(base_dir, "prompts", "code_generator.md")
    
    def _sanitize_var_name(self, name: str) -> str:
        clean = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
        clean = re.sub(r'_+', '_', clean)
        clean = clean.strip('_')
        if clean and clean[0].isdigit():
            clean = f"v_{clean}"
        return clean or "var"

    def generate(self, problem: str, plan: str, variables: dict, previous_code: str = None, error_feedback: str = None) -> str:
        
        # Helper to generate the mandatory casting block
        casting_lines = []
        sanitized_map = {} 

        for original_key, value in variables.items():
            var_name = self._sanitize_var_name(original_key)
            sanitized_map[original_key] = var_name
            
            is_numeric = False
            if isinstance(value, (int, float)):
                is_numeric = True
            elif isinstance(value, str):
                try:
                    float(value)
                    is_numeric = True
                except ValueError:
                    pass
            
            if is_numeric:
                casting_lines.append(f"{var_name} = float(inputs.get('{original_key}', {value}))")
            else:
                casting_lines.append(f"{var_name} = str(inputs.get('{original_key}', '{value}'))")
        
        casting_block = "\n    ".join(casting_lines)
        var_mapping_desc = "\n".join([f"- '{k}' -> variable `{v}`" for k, v in sanitized_map.items()])
        example_var = list(sanitized_map.values())[0] if sanitized_map else 'var'

        # Load Prompt
        try:
            with open(self.prompt_path, "r") as f:
                raw_prompt = f.read()
            
            system_prompt = raw_prompt.replace("{{var_mapping_desc}}", var_mapping_desc)
            system_prompt = system_prompt.replace("{{variables_json}}", json.dumps(variables))
            system_prompt = system_prompt.replace("{{casting_block}}", casting_block)
            system_prompt = system_prompt.replace("{{example_var}}", example_var)
            system_prompt = system_prompt.replace("{{result}}", "{result}") # Restore f-string brace
            
        except Exception as e:
            return f"# Error loading prompt: {e}"

        if previous_code and error_feedback:
            # Refinement Mode
            user_prompt = f"""
            The previous code failed validation.
            
            Error / Feedback:
            {error_feedback}
            
            Previous Code:
            {previous_code}
            
            Please fix the error. 
            Ensure you use the MANDATORY CASTING BLOCK and the Correct Variable Names:
            {var_mapping_desc}
            """
        elif previous_code:
            # Modification Mode
            user_prompt = f"""
            Refactor the following code to meet new requirements.
            
            New Problem: {problem}
            Plan: {plan}
            Original Code:
            {previous_code}
            """
        else:
            # Creation Mode
            user_prompt = f"""
            Problem: {problem}
            Plan: {plan}
            
            Generate the Python code using the template above. Return ONLY the code.
            """

        response = call_llm(system_prompt, user_prompt)
        
        match = re.search(r"```python(.*?)```", response, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            match_generic = re.search(r"```(.*?)```", response, re.DOTALL)
            if match_generic:
                code = match_generic.group(1).strip()
            else:
                code = response.strip()
                
        return code
