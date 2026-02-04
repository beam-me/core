from fastapi import APIRouter, HTTPException, Header, Body
from models import ABNOpenRequest, ABNOpenResponse, ABNAuthorizeRequest
from lib.supabase_client import supabase
from lib.auth import verify_token, create_abn_token
from .orchestrator import authorize_abn 
from agent_registry import registry
import datetime
import uuid

router = APIRouter()

@router.post("/abn/open", response_model=ABNOpenResponse)
async def open_abn_channel(
    req: ABNOpenRequest, 
    authorization: str = Header(None) # Task Token
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Task Token")
    
    try:
        task_claims = verify_token(authorization, expected_prefix="task:")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid Task Token")

    pdp_req = ABNAuthorizeRequest(
        origin_core=req.origin_core,
        target_core=req.target_core,
        proposed_budget=req.proposed_budget
    )
    pdp_res = await authorize_abn(pdp_req)
    
    if not pdp_res.allow:
         raise HTTPException(status_code=403, detail="ABN Authorization Denied by PDP")

    channel_id = f"ch-{uuid.uuid4()}"
    task_id = task_claims.get("sub", "").replace("task:", "")
    
    channel_data = {
        "channel_id": channel_id,
        "task_id": task_id,
        "origin_core": req.origin_core,
        "target_core": req.target_core,
        "negotiation_budget": pdp_res.budget,
        "expires_at": pdp_res.ttl,
        "revoked": False
    }
    
    supabase.table("abn_channels").insert(channel_data).execute()

    abn_token = create_abn_token(
        channel_id=channel_id,
        origin_core=req.origin_core,
        target_core=req.target_core,
        budget=pdp_res.budget,
        allowed_msg_types=pdp_res.allowed_msg_types
    )

    return ABNOpenResponse(
        channel_id=channel_id,
        abn_token=abn_token,
        presigned_upload_url=None
    )

@router.post("/abn/channel/{channel_id}/messages")
async def send_abn_message(
    channel_id: str,
    envelope: dict = Body(...), 
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing ABN Token")
    
    # 1. Verify ABN Token
    try:
        claims = verify_token(authorization, expected_prefix="channel:")
        if claims["sub"] != f"channel:{channel_id}":
            raise HTTPException(status_code=403, detail="Token mismatch for channel")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid ABN Token")

    # 2. Log Transcript (Sender)
    transcript_data = {
        "trace_id": envelope.get("trace_id", str(uuid.uuid4())),
        "channel_id": channel_id,
        "seq": envelope.get("seq", 0),
        "origin_core": envelope.get("origin_core"),
        "target_core": envelope.get("target_core"),
        "msg_type": envelope.get("msg_type"),
        "payload_hash": "hash-placeholder", 
        "payload_path": None,
        "policy_decision": {"allowed": True},
        "gateway_verif": {"valid": True}
    }
    supabase.table("abn_transcripts").insert(transcript_data).execute()

    # 3. Forward to Target (Synchronous RPC for Vercel)
    target_core_id = envelope.get("target_core")
    target_agent = registry.get_agent(target_core_id)
    
    response_payload = None
    if target_agent and hasattr(target_agent, "handle_abn_message"):
        # Invoke the agent
        response_payload = await target_agent.handle_abn_message(envelope)
        
        # Log Reply if exists
        if response_payload:
            reply_transcript = transcript_data.copy()
            reply_transcript["origin_core"] = target_core_id
            reply_transcript["target_core"] = envelope.get("origin_core")
            reply_transcript["msg_type"] = "RESPONSE"
            reply_transcript["seq"] = (envelope.get("seq", 0) + 1)
            supabase.table("abn_transcripts").insert(reply_transcript).execute()
            
    return {"status": "delivered", "reply": response_payload}
