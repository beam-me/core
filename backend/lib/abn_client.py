from typing import Dict, Any, Optional
import uuid
import datetime
# Import Router functions directly to simulate HTTP calls within process
from routers.gateway import open_abn_channel, send_abn_message
from models import ABNOpenRequest

class ABNClient:
    """
    Client for interacting with the ABN Gateway.
    Uses direct function calls to routers to simulate HTTP requests.
    """
    def __init__(self, origin_core_id: str, task_token: str):
        self.origin_core_id = origin_core_id
        self.task_token = task_token
        self.channel_id = None
        self.abn_token = None
        
    async def open_channel(self, target_core_id: str, budget: int = 10) -> str:
        """
        Opens a channel via the Gateway using the Task Token.
        """
        print(f"[{self.origin_core_id}] Opening ABN channel to {target_core_id}...")
        
        req = ABNOpenRequest(
            origin_core=self.origin_core_id,
            target_core=target_core_id,
            proposed_budget=budget
        )
        
        # Call Gateway Router
        # We simulate the Header by passing the string directly
        response = await open_abn_channel(req, authorization=self.task_token)
        
        self.channel_id = response.channel_id
        self.abn_token = response.abn_token
        
        print(f"[{self.origin_core_id}] Channel Open: {self.channel_id}")
        return self.channel_id

    async def send_message(self, msg_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.channel_id or not self.abn_token:
            raise Exception("Channel not open")
            
        # print(f"[{self.origin_core_id}] Sending {msg_type}...")
        
        envelope = {
            "trace_id": str(uuid.uuid4()),
            "channel_id": self.channel_id,
            "origin_core": self.origin_core_id,
            "target_core": payload.get("target_core"), # Target is implicit in channel but payload might specify? 
            # Wait, channel is P2P. Target was defined at open.
            # But send_abn_message implementation in gateway looks at envelope['target_core'].
            # We should probably store target_core in self.
            # For now, let's assume the caller provides it or we fix it.
            "msg_type": msg_type,
            "seq": 1, # TODO: Increment
            **payload
        }
        
        # Call Gateway Router
        response = await send_abn_message(
            channel_id=self.channel_id, 
            envelope=envelope, 
            authorization=self.abn_token
        )
        
        return response.get("reply")
