from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- CORE REGISTRY ---
class CoreRegistrationRequest(BaseModel):
    core_id: str
    public_key_pem: str

# --- TASK TOKEN ---
class TaskRequest(BaseModel):
    task_id: Optional[str] = None
    cores: List[str]
    allow_direct: bool = False

class TaskResponse(BaseModel):
    task_token: str

# --- PDP AUTHORIZATION ---
class ABNAuthorizeRequest(BaseModel):
    origin_core: str
    target_core: str
    proposed_budget: int

class ABNAuthorizeResponse(BaseModel):
    allow: bool
    budget: int
    ttl: str # ISO timestamp or duration string
    allowed_msg_types: List[str]

# --- ABN CHANNEL ---
class ABNOpenRequest(BaseModel):
    origin_core: str
    target_core: str
    proposed_budget: int
    # task_token is sent in Header "Authorization" usually, or separate field if needed

class ABNOpenResponse(BaseModel):
    channel_id: str
    abn_token: str
    presigned_upload_url: Optional[str] = None

# --- MESSAGING ---
class PayloadMeta(BaseModel):
    size_bytes: int
    content_type: str

class Envelope(BaseModel):
    envelope_id: str
    trace_id: str
    channel_id: str
    seq: int
    origin_core: str
    target_core: str
    msg_type: str # PROPOSAL|QUESTION|ARTIFACT_REF|COMMAND|ACK
    payload_hash: str
    payload_meta: PayloadMeta
    signed_by_kid: str
    signature: str
    timestamp: datetime
