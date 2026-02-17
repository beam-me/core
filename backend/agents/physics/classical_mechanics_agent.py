from typing import Dict, Any, List, Optional
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.knowledge_base import KnowledgeBase
from lib.drone_physics import PAVPhysics, RHO_STD # Import Shared Physics
import json
import os
import math

class ClassicalMechanicsAgent(DisciplineCore):
    """
    Agent ID: physics-classical-mechanics-v1
    Role: Solve Newtonian physics problems (Kinematics, Dynamics, Energy).
    Has access to Classical Mechanics Formulas KB.
    Updated with PAV Physics for general aerodynamic calculations.
    """
    name = "physics-classical-mechanics-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, "physics-classical-mechanics-v1")
        
        # Initialize Knowledge Base
        # Path: backend/agents/physics/ -> backend/knowledge
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        kb_path = os.path.join(base_dir, "knowledge", "classical_mechanics_formulas.json")
        self.kb = KnowledgeBase(kb_path)
        
        # Load System Prompt
        self.prompt_path = os.path.join(base_dir, "prompts", "classical_mechanics.md")

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Solve physics problem using Standard Model.",
            "strategy": "Identify Knowns/Unknowns -> Select Formula -> Compute."
        }

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get("objective", "")
        inputs = context.get("inputs", {})
        
        # 1. Retrieve Knowledge (Fetch All Formulas for context)
        # We could filter, but physics problems might need any of them.
        kinematics = self.kb.search("kinematics_suvat")
        dynamics = self.kb.search("dynamics_forces")
        energy = self.kb.search("energy_momentum")
        
        kb_context = f"""
        Physics Formulas:
        Kinematics (SUVAT): {json.dumps(kinematics, indent=2)}
        Dynamics (Forces): {json.dumps(dynamics, indent=2)}
        Energy & Momentum: {json.dumps(energy, indent=2)}
        """
        
        # 2. Check for Aerodynamic specific requests (Basic check)
        # If user asks for "Dynamic Pressure" or similar, we can help calculate it directly.
        extra_context = ""
        if "velocity" in inputs:
            try:
                rho = float(inputs.get("density", RHO_STD))
                v = float(inputs["velocity"])
                # Use Shared Library
                q = PAVPhysics.calc_dynamic_pressure(rho, v)
                extra_context += f"\n[System Note] Calculated Dynamic Pressure (q): {q:.4f} lb/ft^2 (at rho={rho}, V={v})"
            except:
                pass
        
        # 3. Load Prompt
        try:
            with open(self.prompt_path, "r") as f:
                raw_prompt = f.read()
            system_prompt = raw_prompt.replace("{{kb_context}}", kb_context)
            if extra_context:
                system_prompt += extra_context
        except Exception as e:
            return {"error": f"Prompt loading failed: {e}"}
        
        user_prompt = f"""
        Problem: {problem}
        Specific Inputs: {inputs}
        """
        
        # 4. Call LLM (JSON Mode)
        response = call_llm(system_prompt, user_prompt, json_mode=True)
        if not response:
            return {"error": "LLM failed to solve the problem."}
            
        try:
            # Clean and parse
            cleaned = response.replace("```json", "").replace("```", "").strip()
            solution = json.loads(cleaned)
        except Exception as e:
            return {"error": f"JSON PARSE ERROR: {e}", "raw": response}
            
        # Format output for display
        solution["execution_result"] = {
            "stdout": json.dumps(solution, indent=2),
            "stderr": ""
        }
        
        return solution

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in result:
             reason = result["error"]
             if "raw" in result:
                 reason += f" [Raw Output: {str(result['raw'])[:200]}]"
             return {"passed": False, "reason": reason}
        
        # Basic check: Did we get a final answer?
        if "final_answer" not in result:
             return {"passed": False, "reason": "No final answer provided."}
             
        return {"passed": True}
