from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class Task(BaseModel):
    id: str
    description: str
    assigned_core: str
    status: str = "PENDING" # PENDING, IN_PROGRESS, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = []
    metadata: Dict[str, Any] = {} # For passing specific instructions like "Reuse Mode"

class GlobalState(BaseModel):
    run_id: str
    objective: str
    tasks: Dict[str, Task] = {}
    artifacts: Dict[str, Any] = {}
    logs: List[Dict[str, Any]] = []
