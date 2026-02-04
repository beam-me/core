from fastapi import APIRouter, HTTPException, Depends
from models import CoreRegistrationRequest, TaskRequest, TaskResponse, ABNAuthorizeRequest, ABNAuthorizeResponse
from lib.supabase_client import supabase
from lib.auth import create_task_token
import datetime
import uuid

router = APIRouter()

@router.post("/cores/register")
async def register_core(req: CoreRegistrationRequest):
    data = {"core_id": req.core_id, "public_key_pem": req.public_key_pem}
    res = supabase.table("core_registry").upsert(data).execute()
    return {"status": "registered", "core_id": req.core_id}

@router.post("/task", response_model=TaskResponse)
async def create_task(req: TaskRequest):
    task_id = req.task_id or str(uuid.uuid4())
    token = create_task_token(task_id, req.cores, req.allow_direct)
    return TaskResponse(task_token=token)

@router.post("/pdp/authorize_abn", response_model=ABNAuthorizeResponse)
async def authorize_abn(req: ABNAuthorizeRequest):
    # Simple PDP Logic
    MAX_BUDGET = 50
    allowed = req.proposed_budget <= MAX_BUDGET
    
    if not allowed:
        return ABNAuthorizeResponse(
            allow=False, 
            budget=0, 
            ttl="", 
            allowed_msg_types=[]
        )
    
    # Calculate TTL (e.g., 1 hour from now)
    ttl = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
    
    return ABNAuthorizeResponse(
        allow=True,
        budget=req.proposed_budget,
        ttl=ttl,
        allowed_msg_types=["PROPOSAL", "QUESTION", "ARTIFACT_REF", "COMMAND", "ACK"]
    )

@router.delete("/channels/{channel_id}")
async def revoke_channel(channel_id: str):
    supabase.table("abn_channels").update({"revoked": True}).eq("channel_id", channel_id).execute()
    return {"status": "revoked", "channel_id": channel_id}
