from typing import Dict, Any
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.abn_client import ABNClient
from lib.knowledge_base import KnowledgeBase
import json
import os
import sys

class PropulsionSizingAgent(DisciplineCore):
    """
    Agent ID: engineering-propulsion-v1
    Role: Choose motors, props, gearing for required thrust & endurance.
    Has access to a Knowledge Base of components.
    """
    name = "engineering-propulsion-v1" 
    
    def __init__(self, run_id: str):
        super().__init__(run_id, "engineering-propulsion-v1")
        
        # Initialize Knowledge Base
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        kb_path = os.path.join(base_dir, "knowledge", "propulsion_db.json")
        self.kb = KnowledgeBase(kb_path)
        
        # Load System Prompt
        self.prompt_path = os.path.join(base_dir, "prompts", "propulsion_sizing.md")

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Select propulsion components from Knowledge Base and VALIDATE via ABN.",
            "strategy": "1. Search KB. 2. Generate recommendation. 3. Negotiate with Flight Safety."
        }

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get("problem", "")
        inputs = context.get("inputs", {})
        
        # 1. RETRIEVE KNOWLEDGE
        motors = self.kb.search("motors")
        escs = self.kb.search("escs")
        batteries = self.kb.search("batteries")
        
        inventory_context = f"""
        Available Inventory:
        Motors: {json.dumps(motors, indent=2)}
        ESCs: {json.dumps(escs, indent=2)}
        Batteries: {json.dumps(batteries, indent=2)}
        """
        
        self.log("Executor", "Retrieval", "Loaded component inventory from Knowledge Base.", "📚")

        # 2. Load and Format Prompt
        try:
            with open(self.prompt_path, "r") as f:
                raw_prompt = f.read()
            system_prompt = raw_prompt.replace("{{inventory_context}}", inventory_context)
        except Exception as e:
            self.log("System", "Error", f"Failed to load prompt file: {e}", "❌")
            return {"error": "Prompt loading failed."}
        
        user_prompt = f"""
        Requirements: {problem}
        Specific Inputs: {inputs}
        """
        
        print(f"DEBUG: Calling LLM for Propulsion...")
        response = call_llm(system_prompt, user_prompt)
        print(f"DEBUG: LLM Response: {response}")
        sys.stdout.flush()

        if not response:
            return {"error": "LLM failed to generate propulsion recommendation."}
            
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            rec = json.loads(cleaned)
        except Exception as e:
            # CHANGED ERROR MESSAGE TO VERIFY DEPLOYMENT
            return {"error": f"JSON PARSE ERROR: {e}", "raw": response}

        # 3. ABN Negotiation: Check with Flight Safety
        try:
            self.log("Orchestrator", "Request", "Asking Orchestrator for a Safety Expert...", "📡")
            if self.abn:
                abn = self.abn
            else:
                abn = ABNClient(self.name, "legacy-token") 
            
            target_id = await abn.request_connection("Verify flight safety and stability")
            
            if not target_id:
                 self.log("Orchestrator", "Skip", "No Safety Agent available. Skipping validation.", "⏭️")
                 rec["safety_validation"] = "SKIPPED"
            else:
                self.log("ABN", "Connect", f"Channel established with {target_id}.", "🔌")
                
                safety_response = await abn.send_message(
                    target_id,
                    "PROPOSAL",
                    rec
                )
                
                if safety_response:
                    self.log("ABN", "Receive", f"Safety Assessment: {safety_response.get('assessment')}", "📥")
                    rec["safety_validation"] = safety_response
                    if safety_response.get("assessment") == "UNSAFE":
                        rec["status"] = "REJECTED_BY_SAFETY"
                else:
                    rec["safety_validation"] = {"error": "No response"}

        except Exception as e:
            rec["safety_validation"] = {"error": f"ABN Negotiation Failed: {str(e)}"}
            self.log("ABN", "Error", f"Negotiation failed: {str(e)}", "💥")
            
        rec["execution_result"] = {
            "stdout": json.dumps(rec, indent=2),
            "stderr": ""
        }
            
        return rec

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in result:
             reason = result["error"]
             if "raw" in result:
                 reason += f" [Raw Output: {str(result['raw'])[:200]}]"
             return {"passed": False, "reason": reason}
        
        if "performance_estimates" not in result:
             return {"passed": False, "reason": "Missing performance estimates."}
             
        return {"passed": True}
