from typing import Dict, Any, Optional
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.abn_client import ABNClient
from lib.knowledge_base import KnowledgeBase
from lib.drone_physics import PAVPhysics  # Import Shared Physics Library
import json
import os
import sys

class PropulsionSizingAgent(DisciplineCore):
    """
    Agent ID: engineering-propulsion-v1
    Role: Choose motors, props, gearing for required thrust & endurance.
    Has access to a Knowledge Base of components.
    Includes physics-based validation for power requirements using shared PAVPhysics.
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
            "summary": "Select propulsion components from Knowledge Base and VALIDATE via physics + ABN.",
            "strategy": "1. Search KB. 2. Calculate Power Req (Hover/Cruise) using PAVPhysics. 3. Generate recommendation. 4. Negotiate."
        }
    
    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get("problem", "")
        inputs = context.get("inputs", {})
        
        # Extract basic parameters for physics check (if available)
        # Default fallback values used if not provided in inputs
        weight_lbs = float(inputs.get("weight_lbs", 10.0))
        disc_area_ft2 = float(inputs.get("disc_area_ft2", 2.0)) # Approx for a medium quad
        
        # Calculate theoretical power requirements using SHARED LIBRARY
        hover_kw_req = PAVPhysics.calc_hover_power_kw(weight_lbs, disc_area_ft2)
        
        self.log("Executor", "Physics", f"Calculated Hover Power Req: {hover_kw_req:.2f} kW (Weight: {weight_lbs}lbs)", "🧮")

        # 1. RETRIEVE KNOWLEDGE
        motors = self.kb.search("motors")
        escs = self.kb.search("escs")
        batteries = self.kb.search("batteries")
        
        inventory_context = f"""
        Available Inventory:
        Motors: {json.dumps(motors, indent=2)}
        ESCs: {json.dumps(escs, indent=2)}
        Batteries: {json.dumps(batteries, indent=2)}
        
        PHYSICS CONSTRAINTS:
        - Estimated Hover Power Required: {hover_kw_req:.2f} kW
        - Ensure selected motor + battery combination exceeds this value with safety margin.
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
        Calculated Requirements:
        - Hover Power: {hover_kw_req:.2f} kW
        """
        
        # ENABLE JSON MODE
        response = call_llm(system_prompt, user_prompt, json_mode=True)
        
        if not response:
            return {"error": "LLM failed to generate propulsion recommendation."}
            
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            rec = json.loads(cleaned)
            # Inject our calculated value for reference in the output
            rec["physics_calcs"] = {
                "hover_power_kw_required": hover_kw_req,
                "weight_used_lbs": weight_lbs
            }
        except Exception as e:
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
