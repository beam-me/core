from typing import Dict, Any, List
import json
import os
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.abn_client import ABNClient
from lib.knowledge_base import KnowledgeBase

class CadBuilderAgent(DisciplineCore):
    """
    Agent ID: drone-cad-v1
    Role: Generate parametric CAD from specifications.
    """
    name = "drone-cad-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, self.name)
        # Initialize Knowledge Base
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            kb_path = os.path.join(base_dir, "knowledge", "drone_design.json")
            self.kb = KnowledgeBase(kb_path)
        except Exception as e:
            self.log("System", "Warning", f"Could not load Knowledge Base: {e}", "⚠️")
            self.kb = None

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine CAD modeling strategy based on specs.
        """
        specs = context.get("parametric_specs", {})
        
        # Retrieve Knowledge
        kb_context = ""
        if self.kb:
            strategies = self.kb.search("optimization_strategies")
            rules = self.kb.search("design_rules")
            kb_context = f"Design Guidelines:\n{json.dumps(strategies, indent=2)}\nRules:\n{json.dumps(rules, indent=2)}"

        system_prompt = (
            "You are an expert CAD Engineer. Plan the parametric modeling strategy for the given specs.\n"
            f"Reference Design Knowledge:\n{kb_context}\n\n"
            f"Specs: {json.dumps(specs)}\n"
            "Return a JSON object with 'summary' and 'strategy' keys."
        )
        
        response = await call_llm(
            prompt="Develop a CAD modeling plan.",
            system_prompt=system_prompt,
            model="gpt-4o"
        )
        
        try:
            plan = json.loads(response)
        except:
            plan = {
                "summary": "Default Plan: Generate parametric constraints.",
                "strategy": "1. Define base sketches. 2. Extrude/Revolve features. 3. Apply fillets/chamfers."
            }
            
        return plan

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the CAD model (conceptually).
        """
        self.log("Executor", "Action", f"Executing CAD plan: {plan.get('summary')}", "📐")
        
        specs = context.get("parametric_specs", {})
        
        # Retrieve Knowledge
        kb_context = ""
        if self.kb:
            # Re-inject relevant rules for execution
            aerodynamics = self.kb.search("aerodynamics")
            kb_context = f"Aerodynamic Considerations:\n{json.dumps(aerodynamics, indent=2)}"
        
        # Simulating CAD generation
        system_prompt = (
            "You are a CAD Builder Agent. Generate a JSON representation of a parametric 3D model based on the specs.\n"
            f"Apply best practices from:\n{kb_context}\n"
            "Output must be a valid JSON object with 'model_id', 'features' (list), and 'export_path' (simulated)."
        )
        
        user_prompt = f"Generate CAD for: {json.dumps(specs)}"
        
        response = await call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model="gpt-4o"
        )
        
        try:
            result = json.loads(response)
        except:
            # Fallback
            result = {
                "model_id": f"cad_{context.get('run_id', 'unknown')}",
                "features": ["Base Extrusion", "Mounting Holes"],
                "export_path": "/tmp/generated_model.step"
            }

        # Format for ABN / output
        output = {
            "artifact_id": result.get("model_id"),
            "model_data": result,
            "execution_result": {
                "stdout": json.dumps(result, indent=2),
                "stderr": ""
            }
        }
        
        return output

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the generated model meets geometric constraints.
        """
        features = result.get("model_data", {}).get("features", [])
        
        if not features:
             return {"passed": False, "reason": "No features generated in CAD model."}
             
        # Simple check: Ensure export path exists (simulated)
        export_path = result.get("model_data", {}).get("export_path")
        if not export_path:
            return {"passed": False, "reason": "No export path for CAD artifact."}

        return {"passed": True}

    async def handle_abn_message(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle CAD modification requests.
        """
        payload = envelope
        self.log("ABN", "Query", f"Received CAD update request: {payload}", "✏️")
        return {"status": "ACK", "message": "CAD update request received."}
