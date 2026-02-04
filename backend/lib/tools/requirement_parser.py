import json
import os
from lib.llm import call_llm

class RequirementParserTool:
    """
    Tool for extracting variables from natural language.
    Used by Analysis Core Executor.
    """
    
    def __init__(self):
        # Path logic: lib/tools/../../prompts
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.prompt_path = os.path.join(base_dir, "prompts", "requirement_parser.md")

    def parse(self, problem: str, context: dict) -> dict:
        
        try:
            with open(self.prompt_path, "r") as f:
                system_prompt = f.read()
        except Exception as e:
            raise Exception(f"Failed to load prompt file: {e}")

        user_prompt = f"""
        Problem: {problem}
        Current Context: {json.dumps(context)}
        """

        response_text = call_llm(system_prompt, user_prompt)
        if not response_text:
             raise Exception("LLM failed to analyze problem")

        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned_text)
        except Exception:
            raise Exception(f"Invalid JSON from LLM: {cleaned_text}")
