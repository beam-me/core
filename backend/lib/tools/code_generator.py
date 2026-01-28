import json
from ..llm import call_llm

class CodeGeneratorTool:
    """
    Tool for generating Python engineering scripts.
    Used by Engineering Core Executor.
    """
    
    def generate(self, problem: str, plan: str, variables: dict, previous_code: str = None, error_feedback: str = None) -> str:
        
        # Helper to generate the mandatory casting block
        casting_lines = []
        for var_name, value in variables.items():
            # Smart Type Detection
            is_numeric = False
            safe_value = value
            
            if isinstance(value, (int, float)):
                is_numeric = True
            elif isinstance(value, str):
                # Try to parse string as number
                try:
                    float(value)
                    is_numeric = True
                except ValueError:
                    pass
            
            if is_numeric:
                # It's a number (or string number like "10")
                # casting line: var = float(inputs.get('var', value))
                casting_lines.append(f"{var_name} = float(inputs.get('{var_name}', {value}))")
            else:
                # It's definitely a string
                casting_lines.append(f"{var_name} = str(inputs.get('{var_name}', '{value}'))")
        
        casting_block = "\n    ".join(casting_lines)

        system_prompt = f"""
        You are an expert Python engineer for physical simulations.
        Your goal is to write a complete, executable Python script to solve the user's engineering problem.
        
        Constraints:
        1. You MUST use the provided `variables` as the default inputs.
        2. You MUST implement the `get_inputs()` function exactly as shown in the template.
        3. You MUST print the final result to stdout as `Calculated Result: <value>`.
        4. CRITICAL: You MUST use the provided "Casting Block" to ensure type safety.
        
        Template:
        ```python
        import math
        import numpy as np
        import os
        import json

        def get_inputs():
            defaults = {json.dumps(variables)}
            env_input = os.environ.get("BEAM_INPUTS")
            if env_input:
                try:
                    overrides = json.loads(env_input)
                    defaults.update(overrides)
                except Exception:
                    pass
            return defaults

        def solve():
            inputs = get_inputs()
            
            # --- MANDATORY CASTING BLOCK ---
            {casting_block}
            # -------------------------------
            
            # --- CALCULATION SECTION ---
            # Use the variables defined above.
            # Example: area = math.pi * {list(variables.keys())[0] if variables else 'var'} ** 2
            
            # print(f"Calculated Result: {{result}}")
            return True

        if __name__ == "__main__":
            solve()
        ```
        """
        
        if previous_code and error_feedback:
            # Refinement Mode
            user_prompt = f"""
            The previous code failed validation.
            
            Error / Feedback:
            {error_feedback}
            
            Previous Code:
            {previous_code}
            
            Please fix the error by ensuring you use the MANDATORY CASTING BLOCK shown in the template.
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
        
        # Cleanup
        code = response.replace("```python", "").replace("```", "").strip()
        return code
