from typing import Optional

class AgentMatchmaker:
    """
    Simulates the Orchestrator's capability to route requests to the best available agent.
    """
    
    def find_best_agent(self, need_description: str) -> Optional[str]:
        need = need_description.lower()
        
        # Simple rule-based routing for MVP
        if "safety" in need or "stability" in need or "validate" in need:
            return "engineering-flightcontrol-v1"
            
        if "propulsion" in need or "motor" in need:
            return "engineering-propulsion-v1"
            
        if "review" in need or "qa" in need or "security" in need:
            return "qa-codereview-v1"
            
        if "cost" in need:
            # Placeholder if we add CostModelAgent later
            return None
            
        return None

matchmaker = AgentMatchmaker()
