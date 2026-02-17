from typing import Dict, Any, List
import json
import os
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.abn_client import ABNClient
from lib.knowledge_base import KnowledgeBase

class MaterialsAgent(DisciplineCore):
    """
    Agent ID: drone-materials-v1
    Role: Propose materials, fasteners, adhesives, and manufacturing methods.
    """
    name = "drone-materials-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, self.name)
        # Initialize Knowledge Base
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            kb_path = os.path.join(base_dir, "knowledge", "drone_materials.json")
            self.kb = KnowledgeBase(kb_path)
        except Exception as e:
            self.log("System", "Warning", f"Could not load Knowledge Base: {e}", "⚠️")
            self.kb = None

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze part requirements and determine material selection strategy.
        """
        part_specs = context.get("part_specs", {})
        constraints = context.get("constraints", {})
        
        # Retrieve Knowledge
        kb_context = ""
        if self.kb:
            # Get general guidelines
            guidelines = self.kb.search("design_guidelines")
            kb_context = f"Design Guidelines:\n{json.dumps(guidelines, indent=2)}"

        system_prompt = (
            "You are an expert Materials Engineer. Analyze the following part specifications "
            "and constraints to formulate a material selection strategy.\n"
            f"Reference Knowledge:\n{kb_context}\n\n"
            f"Specs: {json.dumps(part_specs)}\n"
            f"Constraints: {json.dumps(constraints)}\n"
            "Return a JSON object with 'summary' and 'strategy' keys."
        )
        
        response = await call_llm(
            prompt="Develop a material selection plan.",
            system_prompt=system_prompt,
            model="gpt-4o"
        )
        
        try:
            plan = json.loads(response)
        except:
            plan = {
                "summary": "Default Plan: Analyze load cases and environmental factors.",
                "strategy": "1. Check load requirements. 2. Verify environmental resistance. 3. Check cost/availability."
            }
            
        return plan

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select materials and generate BOM entries.
        """
        self.log("Executor", "Action", f"Executing plan: {plan.get('summary')}", "🧪")
        
        part_specs = context.get("part_specs", {})

        # Retrieve Knowledge
        kb_context = ""
        if self.kb:
            # Get all filaments
            filaments = self.kb.search("filaments")
            kb_context = f"Available Materials:\n{json.dumps(filaments, indent=2)}"
        
        # Simulating material selection logic
        system_prompt = (
            "You are a Materials Agent. Recommend materials for the given part.\n"
            f"Use the following knowledge base:\n{kb_context}\n"
            "Output must be a valid JSON object with a 'suggestions' list containing objects with: "
            "'material', 'sku', 'yield_pa', 'notes'."
        )
        
        user_prompt = f"Recommend materials for: {json.dumps(part_specs)}"
        
        response = await call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model="gpt-4o"
        )
        
        try:
            result = json.loads(response)
        except:
            # Fallback if LLM fails JSON
            result = {
                "suggestions": [
                    {
                        "material": "Generic Aluminum 6061-T6",
                        "sku": "GEN-AL-6061",
                        "yield_pa": 276000000,
                        "notes": "Standard aerospace grade. (Fallback result)"
                    }
                ]
            }

        # Format for ABN / output
        output = {
            "part_id": part_specs.get("id", "unknown_part"),
            "suggestions": result.get("suggestions", []),
            "execution_result": {
                "stdout": json.dumps(result, indent=2),
                "stderr": ""
            }
        }
        
        return output

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check safety margins and constraints.
        """
        constraints = context.get("constraints", {})
        min_yield = constraints.get("min_yield_pa", 0)
        
        suggestions = result.get("suggestions", [])
        if not suggestions:
            return {"passed": False, "reason": "No material suggestions generated."}
            
        for suggestion in suggestions:
            mat_yield = suggestion.get("yield_pa", 0)
            if mat_yield < min_yield:
                 return {
                     "passed": False, 
                     "reason": f"Material {suggestion.get('material')} yield {mat_yield} < required {min_yield}"
                 }

        return {"passed": True}

    async def handle_abn_message(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle inquiries about material properties.
        """
        payload = envelope
        self.log("ABN", "Query", f"Received material query: {payload}", "🔬")
        return {"status": "ACK", "message": "Material query received."}
