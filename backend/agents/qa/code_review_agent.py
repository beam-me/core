from typing import Dict, Any
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.knowledge_base import KnowledgeBase
import json
import os

class CodeReviewAgent(DisciplineCore):
    """
    Agent ID: qa-codereview-v1
    Role: Review code for security vulnerabilities, bugs, and best practices.
    Has access to a Security Vulnerability Knowledge Base.
    """
    name = "qa-codereview-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, "qa-codereview-v1")
        # Initialize Knowledge Base
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        kb_path = os.path.join(base_dir, "knowledge", "security_vulns.json")
        self.kb = KnowledgeBase(kb_path)
        
        # Load System Prompt
        self.prompt_path = os.path.join(base_dir, "prompts", "code_review.md")

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"strategy": "Static analysis via LLM with Security KB check."}

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        code = context.get("code", "")
        if not code:
            return {"error": "No code provided for review."}
            
        # Retrieve Knowledge
        banned = self.kb.search("banned_functions")
        cwes = self.kb.search("common_cwes")
        
        kb_context = f"""
        Security Knowledge Base:
        Banned Functions: {json.dumps(banned, indent=2)}
        Common Weaknesses: {json.dumps(cwes, indent=2)}
        """
        
        # Load Prompt
        try:
            with open(self.prompt_path, "r") as f:
                raw_prompt = f.read()
            system_prompt = raw_prompt.replace("{{kb_context}}", kb_context)
        except Exception as e:
            return {"error": f"Prompt loading failed: {e}"}
        
        response = call_llm(system_prompt, f"Code:\n{code}")
        try:
            return json.loads(response.replace("```json", "").replace("```", "").strip())
        except:
            return {"error": "Failed to parse review", "raw": response}

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True}

    async def handle_abn_message(self, envelope: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        code = payload.get("code")
        context = {"code": code}
        review_result = await self._execute({}, context)
        return review_result
