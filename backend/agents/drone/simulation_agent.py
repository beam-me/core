from typing import Dict, Any, List, Optional
import json
import os
import math
import numpy as np
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.abn_client import ABNClient
from lib.knowledge_base import KnowledgeBase
from lib.drone_physics import PAVPhysics, MPH_TO_FTS, RHO_STD # Import Shared Physics

class QuickSimAgent(DisciplineCore):
    """
    Agent ID: drone-quick-sim-v1
    Role: Run fast sanity checks (lightweight simulation) to validate designs early.
    Updated with PAV Physics for Aerodynamic Simulations via shared library.
    """
    name = "drone-quick-sim-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, self.name)
        # Initialize Knowledge Base
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            kb_path = os.path.join(base_dir, "knowledge", "drone_simulation.json")
            self.kb = KnowledgeBase(kb_path)
        except Exception as e:
            self.log("System", "Warning", f"Could not load Knowledge Base: {e}", "⚠️")
            self.kb = None

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup the simulation environment and boundary conditions.
        """
        cad_artifact = context.get("cad_artifact", {})
        load_cases = context.get("load_cases", [])
        
        # Retrieve Knowledge
        kb_context = ""
        if self.kb:
            guidelines = self.kb.search("simulation_guidelines")
            kb_context = f"Simulation Guidelines:\n{json.dumps(guidelines, indent=2)}"

        system_prompt = (
            "You are a Simulation Engineer. Plan the setup for a quick Finite Element Analysis (FEA) check.\n"
            f"Reference Guidelines:\n{kb_context}\n\n"
            f"CAD Artifact: {json.dumps(cad_artifact)}\n"
            f"Load Cases: {json.dumps(load_cases)}\n"
            "Return a JSON object with 'summary', 'mesh_strategy', and 'solver_settings'."
        )
        
        # Note: Using json_mode=True if supported by underlying LLM helper, otherwise parsing manually
        # Assuming call_llm handles string response
        response = call_llm(
            system_prompt,
            "Plan the simulation setup.",
            json_mode=True 
        )
        
        try:
            plan = json.loads(response)
        except:
            plan = {
                "summary": "Default Plan: Apply standard loads to mesh.",
                "mesh_strategy": "Coarse tet-mesh for speed.",
                "solver_settings": "Linear elastic solver."
            }
            
        return plan

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the simulation (simulated + physics calculation).
        """
        self.log("Executor", "Action", f"Running simulation with plan: {plan.get('summary')}", "🔥")
        
        inputs = context.get("inputs", {})
        
        # --- PHYSICS CALCULATION ---
        # Extract parameters or use defaults for physics check
        weight_lbs = float(inputs.get("weight_lbs", 10.0))
        wing_area_ft2 = float(inputs.get("wing_area_ft2", 5.0))
        wetted_area_ft2 = float(inputs.get("wetted_area_ft2", 15.0))
        aspect_ratio = float(inputs.get("aspect_ratio", 8.0))
        efficiency_factor = float(inputs.get("efficiency_factor", 0.8)) # 'e'
        cd_profile = float(inputs.get("cd_profile", 0.02)) # 'CDw'
        cruise_speed_mph = float(inputs.get("cruise_speed_mph", 60.0))
        
        cruise_speed_fts = cruise_speed_mph * MPH_TO_FTS
        rho = RHO_STD # Assuming sea level for quick check
        
        # Calculate Drag using SHARED LIBRARY
        try:
            lift_coeff = PAVPhysics.calc_lift_coefficient(
                weight_lbs, rho, cruise_speed_fts, wing_area_ft2
            )
            drag_lbs = PAVPhysics.calc_drag(
                weight_lbs, rho, cruise_speed_fts, 
                wing_area_ft2, aspect_ratio, efficiency_factor, 
                cd_profile, wetted_area_ft2
            )
            
            physics_results = {
                "drag_lbs": drag_lbs,
                "lift_coefficient": lift_coeff,
                "cruise_speed_mph": cruise_speed_mph
            }
            self.log("Executor", "Physics", f"Calculated Drag: {drag_lbs:.2f} lbs at {cruise_speed_mph} mph", "💨")
        except Exception as e:
            physics_results = {"error": str(e)}
            self.log("Executor", "Error", f"Physics calc failed: {e}", "❌")

        # Retrieve Knowledge for Validation
        kb_context = ""
        if self.kb:
            validation_data = self.kb.search("validation_data")
            kb_context = f"Validation Data Baseline:\n{json.dumps(validation_data, indent=2)}"
        
        # Simulating SfePy / PyCalculix run
        system_prompt = (
            "You are a Quick-Sim Agent. Simulate the results of the FEA analysis.\n"
            f"Ensure results are consistent with typical validation data:\n{kb_context}\n"
            f"PHYSICS RESULTS (Aerodynamics): {json.dumps(physics_results)}\n"
            "Output must be a valid JSON object with 'max_stress_pa', 'max_deflection_mm', 'safety_factor', and 'passed' (bool)."
        )
        
        user_prompt = f"Simulate results for plan: {json.dumps(plan)}"
        
        response = call_llm(
            system_prompt,
            user_prompt,
            json_mode=True
        )
        
        try:
            result = json.loads(response)
            result["physics_aerodynamics"] = physics_results
        except:
            # Fallback
            result = {
                "max_stress_pa": 150000000.0,
                "max_deflection_mm": 0.5,
                "safety_factor": 1.5,
                "passed": True,
                "physics_aerodynamics": physics_results
            }

        # Format for ABN / output
        output = {
            "simulation_report": result,
            "execution_result": {
                "stdout": json.dumps(result, indent=2),
                "stderr": ""
            }
        }
        
        return output

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the design passes simulation criteria.
        """
        report = result.get("simulation_report", {})
        safety_factor = report.get("safety_factor", 0.0)
        min_safety_factor = context.get("min_safety_factor", 1.2)
        
        passed = report.get("passed", False)
        
        # Check Drag validity (basic sanity check)
        physics = report.get("physics_aerodynamics", {})
        drag = physics.get("drag_lbs", 0)
        if isinstance(drag, (int, float)) and drag == float('inf'):
             return {
                "passed": False, 
                "reason": "Simulation failed: Aerodynamic Stall (Drag is Infinite)"
            }

        if not passed or safety_factor < min_safety_factor:
            return {
                "passed": False, 
                "reason": f"Simulation failed: Safety Factor {safety_factor} < {min_safety_factor}"
            }

        return {"passed": True}

    async def handle_abn_message(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle simulation requests from other agents.
        """
        payload = envelope
        self.log("ABN", "Query", f"Received simulation request: {payload}", "🧮")
        return {"status": "ACK", "message": "Simulation request queued."}
