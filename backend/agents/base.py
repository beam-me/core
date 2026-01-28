from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class AgentState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_USER = "AWAITING_USER"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    from_agent: str
    to_agent: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.isoformat(datetime.now()))
    state: AgentState
    summary: str
    confidence: float
    payload: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)

class BaseAgent:
    name: str = "base-agent"
    version: str = "v0.1"

    def __init__(self, run_id: str):
        self.run_id = run_id

    async def run(self, input_payload: Dict[str, Any]) -> AgentMessage:
        raise NotImplementedError("Agents must implement run()")
