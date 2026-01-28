import json
from ..llm import call_llm

class RequirementParserTool:
    """
    Tool for extracting variables from natural language.
    Used by Analysis Core Executor.
    """
    
    def parse(self, problem: str, context: dict) -> dict:
        system_prompt = """
        You are an expert mechanical engineering assistant.
        Your goal is to analyze a problem description and determine if you have enough information to solve it using a Python script.
        
        STRICT RULES:
        1. You must identify specific physical parameters (Radius, Length, Force, Material, etc.).
        2. DO NOT assume defaults for these primary variables. You MUST ask the user for them.
        3. Only assume defaults for universal constants (Gravity = 9.81, Density of Steel = 7850, etc.).
        4. If the user provided values in 'Current Context', use them.
        
        If you need more information, return a JSON object with:
        {
            "status": "MISSING_INFO",
            "reasoning": "Brief explanation...",
            "missing_vars": [
                {"name": "var_name", "type": "number|string", "description": "Question to ask user", "default": 10.0}
            ]
        }

        If you have enough information, return:
        {
            "status": "READY",
            "variables": { "var_name": value, ... },
            "plan": "Description of the solution steps"
        }
        """

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
