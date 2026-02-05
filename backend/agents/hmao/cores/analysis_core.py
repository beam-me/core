from typing import Dict, Any
# ABSOLUTE IMPORT FIX
from agents.hmao.core import DisciplineCore
from lib.tools.requirement_parser import RequirementParserTool
from lib.knowledge_base import KnowledgeBase
import json
import os

class AnalysisCore(DisciplineCore):
    """
    Core ID: analysis_core
    Responsibility: Requirement Analysis & Variable Extraction.
    Has access to Physics Constants KB.
    """
    def __init__(self, run_id: str):
        super().__init__(run_id, "analysis_core")
        self.parser = RequirementParserTool()
        
        # Initialize Knowledge Base
        # Path logic: backend/agents/hmao/cores/analysis_core.py -> backend/knowledge
        # Needs 4 dirnames
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        kb_path = os.path.join(base_dir, "knowledge", "physics_constants.json")
        self.kb = KnowledgeBase(kb_path)

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Extract physical variables from natural language.",
            "strategy": "Use LLM to parse user prompt into JSON schema with KB context."
        }

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Retrieve Knowledge
        constants = self.kb.search("constants")
        units = self.kb.search("common_units")
        
        kb_data = {
            "physics_constants": constants,
            "unit_conversions": units
        }
        
        # Inject KB into artifacts for the Parser Tool
        artifacts = context.get("artifacts", {}).copy()
        artifacts["knowledge_base"] = kb_data
        
        try:
            parsed_data = self.parser.parse(
                problem=context.get("objective", ""),
                context=artifacts 
            )
            return parsed_data
        except Exception as e:
            return {"error": str(e)}

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in result:
            return {"passed": False, "reason": result["error"]}

        if result.get("status") == "MISSING_INFO":
            if "missing_vars" in result:
                return {"passed": True}
            else:
                return {"passed": False, "reason": "MISSING_INFO status but no variables requested."}

        variables = result.get("variables", {})
        if not isinstance(variables, dict):
            return {"passed": False, "reason": "Variables must be a dictionary."}
        
        return {"passed": True}
