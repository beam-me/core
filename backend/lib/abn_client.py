from typing import Dict, Any, Optional
import uuid
import datetime
# Import Router functions directly to simulate HTTP calls within process
from routers.gateway import open_abn_channel, send_abn_message
from models import ABNOpenRequest
from lib.matchmaker import matchmaker

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
        
    async def request_connection(self, need_description: str) -> Optional[str]:
        """
        Ask the Orchestrator to find a peer and open a channel.
        Returns the target_core_id if successful.
        """
        print(f"[{self.origin_core_id}] Requesting connection for: {need_description}")
        
        # 1. Ask Orchestrator (Matchmaker)
        target_id = matchmaker.find_best_agent(need_description)
        
        if not target_id:
            print(f"Orchestrator could not find agent for: {need_description}")
            return None
            
        print(f"Orchestrator selected: {target_id}")
        
        # 2. Open Channel
        await self.open_channel(target_id)
        
        if self.channel_id:
            return target_id
        return None

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

    async def send_message(self, target_core_id: str, msg_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Note: target_core_id arg is kept for compatibility with agent code, 
        # but the channel is already bound to a target.
        # We should verify it matches or just ignore it.
        
        if not self.channel_id or not self.abn_token:
            raise Exception("Channel not open")
            
        # print(f"[{self.origin_core_id}] Sending {msg_type}...")
        
        envelope = {
            "trace_id": str(uuid.uuid4()),
            "channel_id": self.channel_id,
            "origin_core": self.origin_core_id,
            "target_core": target_core_id, 
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
