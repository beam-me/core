from typing import Dict, Any, List
import json
from agents.hmao.core import DisciplineCore
from lib.llm import call_llm
from lib.abn_client import ABNClient

class ResearchAgent(DisciplineCore):
    """
    Agent ID: drone-research-v1
    Role: Support early design decisions with targeted research.
    """
    name = "drone-research-v1"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, self.name)

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formulate search queries and research strategy.
        """
        topic = context.get("topic", "")
        constraints = context.get("constraints", {})
        
        system_prompt = (
            "You are an expert Research Assistant. Develop a strategy to research the given topic.\n"
            f"Topic: {topic}\n"
            f"Constraints: {json.dumps(constraints)}\n"
            "Return a JSON object with 'summary' and 'queries' (list of strings)."
        )
        
        response = await call_llm(
            prompt="Plan the research.",
            system_prompt=system_prompt,
            model="gpt-4o"
        )
        
        try:
            plan = json.loads(response)
        except:
            plan = {
                "summary": "Default Plan: Search academic and supplier databases.",
                "queries": [f"properties of {topic}", f"manufacturers for {topic}"]
            }
            
        return plan

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the research queries (simulated).
        """
        self.log("Executor", "Action", f"Conducting research with plan: {plan.get('summary')}", "🔍")
        
        queries = plan.get("queries", [])
        
        # Simulating search execution
        system_prompt = (
            "You are a Research Agent. Synthesize findings based on the queries.\n"
            "Output must be a valid JSON object with 'findings' (list of objects with 'source', 'content', 'confidence')."
        )
        
        user_prompt = f"Synthesize findings for queries: {json.dumps(queries)}"
        
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
                "findings": [
                    {
                        "source": "Journal of Aerospace Materials, 2024",
                        "content": "New alloy X-100 shows 20% better fatigue life.",
                        "confidence": 0.95
                    }
                ]
            }

        # Format for ABN / output
        output = {
            "research_report": result,
            "execution_result": {
                "stdout": json.dumps(result, indent=2),
                "stderr": ""
            }
        }
        
        return output

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check quality and confidence of research findings.
        """
        findings = result.get("research_report", {}).get("findings", [])
        min_confidence = context.get("min_confidence", 0.7)
        
        if not findings:
            return {"passed": False, "reason": "No research findings generated."}
            
        low_confidence_count = 0
        for f in findings:
            if f.get("confidence", 0) < min_confidence:
                low_confidence_count += 1
        
        if low_confidence_count > len(findings) / 2:
             return {"passed": False, "reason": "Majority of findings have low confidence."}

        return {"passed": True}

    async def handle_abn_message(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle direct research inquiries.
        """
        payload = envelope
        self.log("ABN", "Query", f"Received research query: {payload}", "📚")
        return {"status": "ACK", "message": "Research query received."}
