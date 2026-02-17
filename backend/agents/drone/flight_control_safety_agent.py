from typing import Dict, Any
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.knowledge_base import KnowledgeBase
import json
import os

class FlightControlSafetyAgent(DisciplineCore):
    """
    Agent ID: engineering-flightcontrol-v1
    Role: Validate control gains vs manufacturing variance.
    Has access to Safety Regulations KB.
    """
    name = "engineering-flightcontrol-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, "engineering-flightcontrol-v1")
        # Initialize Knowledge Base
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        kb_path = os.path.join(base_dir, "knowledge", "safety_regulations.json")
        self.kb = KnowledgeBase(kb_path)
        
        # Load System Prompt
        self.prompt_path = os.path.join(base_dir, "prompts", "flight_safety.md")

    async def handle_abn_message(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = envelope
        context = {
            "artifacts": {"propulsion_recommendation": payload},
            "objective": "ABN Negotiation: Validate this proposal."
        }
        plan = {"strategy": "ABN Validation"}
        return await self._execute(plan, context)

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Assess flight stability and safety risks.",
            "strategy": "Evaluate proposed configuration against KB criteria."
        }

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        artifacts = context.get("artifacts", {})
        propulsion_rec = artifacts.get("propulsion_recommendation", {})
        
        # Retrieve Knowledge
        margins = self.kb.search("stability_margins")
        limits = self.kb.search("environmental_limits")
        
        kb_context = f"""
        Safety Regulations:
        Stability Margins: {json.dumps(margins, indent=2)}
        Environmental Limits: {json.dumps(limits, indent=2)}
        """
        
        # Load Prompt
        try:
            with open(self.prompt_path, "r") as f:
                raw_prompt = f.read()
            system_prompt = raw_prompt.replace("{{kb_context}}", kb_context)
        except Exception as e:
            return {"error": f"Prompt loading failed: {e}"}
        
        user_prompt = f"""
        Analyzing Configuration:
        {json.dumps(propulsion_rec, indent=2)}
        
        General Requirements: {context.get("objective", "")}
        """
        
        # ENABLE JSON MODE
        response = call_llm(system_prompt, user_prompt, json_mode=True)
        if not response:
            return {"error": "LLM failed to generate safety assessment."}
            
        try:
             cleaned = response.replace("```json", "").replace("```", "").strip()
             return json.loads(cleaned)
        except Exception as e:
            return {"error": f"Failed to parse safety assessment: {e}", "raw": response}

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in result:
             reason = result["error"]
             if "raw" in result:
                 reason += f" [Raw Output: {str(result['raw'])[:200]}]"
             return {"passed": False, "reason": reason}
        
        if result.get("assessment") == "UNSAFE":
             return {"passed": True, "warning": "Configuration deemed UNSAFE. Redesign recommended."}
             
        return {"passed": True}
