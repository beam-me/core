from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import sys
import os
import traceback

# Fix path to allow importing from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import HMAO Orchestrator (Replaces BeamRouter)
from agents.hmao.orchestrator import GlobalOrchestrator
from agent_registry import AGENT_REGISTRY
# Import Supabase
from lib.supabase_client import supabase
# Import Git Check
from lib.git_check import check_git_connection
# Import Indexer
from lib.indexer import search_similar_code

load_dotenv()

app = FastAPI(title="Beam.me HMAO Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartRunRequest(BaseModel):
    problem_description: str

class ContinueRunRequest(BaseModel):
    run_id: str
    problem_description: str
    inputs: Dict[str, Any]

@app.get("/api")
async def root():
    return {"message": "Beam.me HMAO Orchestrator is running", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "cwd": os.getcwd(),
        "path": sys.path
    }

@app.get("/api/health/db")
async def health_check_db():
    try:
        response = supabase.storage.list_buckets()
        return {
            "status": "connected",
            "buckets": response
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/health/git")
async def health_check_git():
    return check_git_connection()

@app.get("/api/history")
async def get_history():
    try:
        # Fetch last 20 code artifacts
        response = supabase.table("code_artifacts")\
            .select("run_id, problem_description, created_at, file_path, metadata")\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        return response.data
    except Exception as e:
        print(f"History Fetch Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{run_id}")
async def delete_history_item(run_id: str):
    try:
        response = supabase.table("code_artifacts").delete().eq("run_id", run_id).execute()
        return {"status": "deleted", "run_id": run_id}
    except Exception as e:
        print(f"Delete Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def get_agents():
    return AGENT_REGISTRY

@app.post("/api/run/start")
async def start_run(request: StartRunRequest):
    try:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        # Use GlobalOrchestrator
        orchestrator = GlobalOrchestrator(run_id=run_id)
        result = await orchestrator.run({"problem": request.problem_description})
        return result
    except Exception as e:
        error_msg = f"Server Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/run/continue")
async def continue_run(request: ContinueRunRequest):
    try:
        # Resume the run with the provided inputs
        # Use GlobalOrchestrator
        orchestrator = GlobalOrchestrator(run_id=request.run_id)
        
        # Pass inputs to Orchestrator
        result = await orchestrator.run({
            "problem": request.problem_description,
            "inputs": request.inputs
        })
        return result
    except Exception as e:
        error_msg = f"Server Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# DEBUG ENDPOINTS
@app.get("/api/debug/artifacts")
async def list_artifacts():
    try:
        response = supabase.table("code_artifacts").select("*").limit(10).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/search")
async def debug_search(q: str):
    try:
        results = search_similar_code(q, threshold=0.1, limit=5)
        return {"query": q, "results": results}
    except Exception as e:
        return {"error": str(e)}
