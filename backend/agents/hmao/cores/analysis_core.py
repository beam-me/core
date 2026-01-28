from typing import Dict, Any
# ABSOLUTE IMPORT FIX
from agents.hmao.core import DisciplineCore
from lib.tools.requirement_parser import RequirementParserTool

class AnalysisCore(DisciplineCore):
    """
    Core ID: analysis_core
    Responsibility: Requirement Analysis & Variable Extraction
    """
    def __init__(self, run_id: str):
        super().__init__(run_id, "analysis_core")
        self.parser = RequirementParserTool()

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Extract physical variables from natural language.",
            "strategy": "Use LLM to parse user prompt into JSON schema."
        }

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # The Executor uses the Requirement Parser Tool
        # FIXED: Use 'objective' (User's Goal) instead of 'task' (Internal Instruction)
        # This ensures the Parser analyzes the actual physics problem, not the meta-task.
        try:
            parsed_data = self.parser.parse(
                problem=context.get("objective", ""),
                context=context.get("artifacts", {})
            )
            return parsed_data
        except Exception as e:
            # If tool fails, return error payload (Validation will catch it)
            return {"error": str(e)}

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic Check
        if "error" in result:
            return {"passed": False, "reason": result["error"]}

        # If Status is MISSING_INFO, we allow it (Orchestrator handles Awaiting User)
        if result.get("status") == "MISSING_INFO":
            if "missing_vars" in result:
                return {"passed": True}
            else:
                return {"passed": False, "reason": "MISSING_INFO status but no variables requested."}

        variables = result.get("variables", {})
        if not isinstance(variables, dict):
            return {"passed": False, "reason": "Variables must be a dictionary."}
        
        return {"passed": True}
