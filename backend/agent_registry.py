from typing import List, Dict, Any, Optional

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._profiles: List[Dict[str, Any]] = []

    def register(self, agent: Any):
        # Prioritize 'agent_id', then 'name', then class name
        agent_id = getattr(agent, "agent_id", getattr(agent, "name", str(agent.__class__.__name__)))
        self._agents[agent_id] = agent
        # Also store profile if available
        if hasattr(agent, "profile"):
            self._profiles.append(agent.profile)

    def get_agent(self, agent_id: str) -> Optional[Any]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        # Return profiles or basic info
        return self._profiles

registry = AgentRegistry()

# Legacy static data (kept for reference if needed)
AGENT_REGISTRY_DATA = [
    {
        "id": "hmao.orchestrator",
        "name": "Global Orchestrator",
        # ... (rest of the static data)
    }
]
