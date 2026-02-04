import jwt
import os
import datetime
from typing import Dict, List, Any, Optional

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-dev-key")
ALGORITHM = "HS256"

def create_task_token(task_id: str, cores: List[str], allow_direct: bool = False, expires_in_hours: int = 1) -> str:
    payload = {
        "iss": "orchestrator.beam.me",
        "sub": f"task:{task_id}",
        "cores": cores,
        "allow_direct": allow_direct,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def create_abn_token(channel_id: str, origin_core: str, target_core: str, budget: int, allowed_msg_types: List[str], expires_in_hours: int = 1) -> str:
    payload = {
        "iss": "orchestrator.beam.me",
        "sub": f"channel:{channel_id}",
        "origin_core": origin_core,
        "target_core": target_core,
        "negotiation_budget": budget,
        "allowed_msg_types": allowed_msg_types,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def verify_token(token: str, expected_prefix: Optional[str] = None) -> Dict[str, Any]:
    try:
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        
        if expected_prefix:
            if not payload.get("sub", "").startswith(expected_prefix):
                 raise Exception(f"Invalid token scope. Expected {expected_prefix}")
                 
        return payload
    except Exception as e:
        raise Exception(f"Token verification failed: {str(e)}")
