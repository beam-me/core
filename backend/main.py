import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import Routers
from routers import orchestrator, gateway

# Import Agents (Original functionality)
from agent_registry import registry
from agents.hmao.orchestrator import GlobalOrchestrator
from agents.hmao.cores.analysis_core import AnalysisCore
from agents.hmao.cores.engineering_core import EngineeringCore
from agents.drone.propulsion_sizing_agent import PropulsionSizingAgent
from agents.drone.flight_control_safety_agent import FlightControlSafetyAgent
from agents.qa.code_review_agent import CodeReviewAgent

load_dotenv()

app = FastAPI(title="Beam.me Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register ABN Routers
app.include_router(orchestrator.router, tags=["Orchestrator"])
app.include_router(gateway.router, tags=["Gateway"])

# Register Agents
registry.register(GlobalOrchestrator("sys"))
registry.register(AnalysisCore("sys"))
registry.register(EngineeringCore("sys"))
registry.register(PropulsionSizingAgent("sys"))
registry.register(FlightControlSafetyAgent("sys"))
registry.register(CodeReviewAgent("sys"))

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Beam.me Orchestrator & Gateway"}

# --- ORIGINAL RUN ENDPOINTS (Preserved for Frontend Compatibility) ---
from pydantic import BaseModel

class RunStartRequest(BaseModel):
    problem_description: str

class RunContinueRequest(BaseModel):
    run_id: str
    problem_description: str
    inputs: dict = {}

@app.post("/api/run/start")
async def start_run(req: RunStartRequest):
    # Determine which agent to start with (Orchestrator usually)
    # Using "hmao.orchestrator" as defined in GlobalOrchestrator.name
    agent_class = registry.get_agent("hmao.orchestrator")
    if not agent_class:
        return {"error": "Orchestrator not found"}
    
    # Instantiate the agent for this run
    run_id = f"run-{os.urandom(4).hex()}"
    # The registry stores the CLASS or INSTANCE?
    # My registry code: registry.register(GlobalOrchestrator("sys")) stores an INSTANCE.
    # So agent_class is actually an INSTANCE.
    # BUT, we need a NEW instance for a new run.
    # Refactoring registry usage:
    # Option A: Registry stores classes.
    # Option B: Registry stores a "System" instance, and we use it as a factory.
    
    # In my previous registry update, I registered GlobalOrchestrator("sys").
    # So `registry.get_agent` returns that instance.
    # That instance has state! This is bad for concurrent runs if I reuse it.
    # Ideally, I should register the CLASS.
    
    # Quick fix: Use the class directly since I know it here.
    # Or rely on the fact that for Vercel (serverless), memory is ephemeral per request usually, 
    # but concurrent requests might share the process.
    
    # Better approach: Instantiate fresh here.
    agent = GlobalOrchestrator(run_id)
    
    # Execute the Agent (Run until pause or completion)
    # This might take 5-10s.
    result_msg = await agent.run({
        "problem": req.problem_description,
        "inputs": {}
    })
    
    # Map AgentMessage to Frontend Response
    response = {
        "run_id": run_id,
        "state": result_msg.state, 
        "problem_description": req.problem_description,
        "payload": {
            "trace_log": agent.state.logs, # Use the logs from the agent state
            "missing_vars": result_msg.payload.get("missing_vars", []),
            "execution_result": result_msg.payload.get("execution_result", {}),
            "code_url": result_msg.payload.get("code_url")
        }
    }
    
    return response

@app.post("/api/run/continue")
async def continue_run(req: RunContinueRequest):
    # Re-instantiate agent (Stateless mode: Re-run with new inputs)
    agent = GlobalOrchestrator(req.run_id)
    
    result_msg = await agent.run({
        "problem": req.problem_description,
        "inputs": req.inputs # User provided variables
    })

    return {
        "run_id": req.run_id,
        "state": result_msg.state,
        "problem_description": req.problem_description,
        "payload": {
            "trace_log": agent.state.logs,
            "missing_vars": result_msg.payload.get("missing_vars", []),
            "execution_result": result_msg.payload.get("execution_result", {}),
            "code_url": result_msg.payload.get("code_url")
        }
    }

@app.get("/api/history")
async def get_history():
    return []

@app.get("/api/agents")
async def get_agents():
    # Return mock profiles for the frontend visualization
    return [
        {
            "id": "hmao-orchestrator",
            "name": "Orchestrator",
            "role": "Mission Control",
            "icon": "🧠",
            "description": "Manages the overall mission lifecycle and delegates tasks.",
            "instructions": ["Ensure safety", "Optimize budget"],
            "tools": ["planner", "delegator"],
            "relationships": {"incoming": [], "outgoing": ["engineering-core"]}
        },
        {
            "id": "engineering-core",
            "name": "Engineering Core",
            "role": "Builder",
            "icon": "🛠️",
            "description": "Implements code solutions and runs simulations.",
            "instructions": ["Write clean code", "Verify outputs"],
            "tools": ["code_gen", "linter"],
            "relationships": {"incoming": ["hmao-orchestrator"], "outgoing": []}
        },
        {
            "id": "engineering-propulsion-v1",
            "name": "Propulsion Sizing",
            "role": "Drone Specialist",
            "icon": "🚁",
            "description": "Selects motors, props, and batteries for flight requirements.",
            "instructions": ["Maximize endurance", "Ensure T/W ratio > 2"],
            "tools": ["component_db", "thrust_calc"],
            "relationships": {"incoming": ["hmao-orchestrator"], "outgoing": ["engineering-flightcontrol-v1"]}
        },
        {
            "id": "engineering-flightcontrol-v1",
            "name": "Flight Safety",
            "role": "Safety Critic",
            "icon": "🛡️",
            "description": "Validates stability margins and assesses crash risk.",
            "instructions": ["Check PID margins", "Verify vibration limits"],
            "tools": ["stability_sim", "risk_model"],
            "relationships": {"incoming": ["engineering-propulsion-v1"], "outgoing": []}
        },
        {
            "id": "qa-codereview-v1",
            "name": "QA Reviewer",
            "role": "Auditor",
            "icon": "🧐",
            "description": "Reviews code for bugs and security issues.",
            "instructions": ["Check PEP8", "Find security holes"],
            "tools": ["static_analysis"],
            "relationships": {"incoming": ["engineering-core"], "outgoing": []}
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
