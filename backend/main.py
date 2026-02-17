import os
import sys
import re

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
from agents.physics.classical_mechanics_agent import ClassicalMechanicsAgent
# NEW DRONE AGENTS
from agents.drone.materials_agent import MaterialsAgent
from agents.drone.cad_agent import CadBuilderAgent
from agents.drone.simulation_agent import QuickSimAgent
from agents.drone.research_agent import ResearchAgent

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
registry.register(ClassicalMechanicsAgent("sys"))
# NEW DRONE AGENTS REGISTRATION
registry.register(MaterialsAgent("sys"))
registry.register(CadBuilderAgent("sys"))
registry.register(QuickSimAgent("sys"))
registry.register(ResearchAgent("sys"))

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

def generate_readable_run_id(problem: str) -> str:
    """
    Generates a human-readable slug from the problem description.
    Ex: "Design a heavy lift drone" -> "design-heavy-lift-drone-a1b2"
    """
    # 1. Lowercase and remove special chars
    if not problem:
        return f"run-{os.urandom(4).hex()}"
        
    slug = re.sub(r'[^a-z0-9\s-]', '', problem.lower())
    # 2. Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # 3. Truncate to 4-5 words
    parts = slug.split('-')[:5]
    if not parts:
        return f"run-{os.urandom(4).hex()}"
        
    base_slug = '-'.join(parts)
    # 4. Append short random suffix for uniqueness
    suffix = os.urandom(2).hex()
    return f"{base_slug}-{suffix}"

@app.post("/api/run/start")
async def start_run(req: RunStartRequest):
    agent_class = registry.get_agent("hmao.orchestrator")
    if not agent_class:
        return {"error": "Orchestrator not found"}
    
    # Generate Readable ID
    run_id = generate_readable_run_id(req.problem_description)
    
    # Instantiate fresh for this run
    agent = GlobalOrchestrator(run_id)
    
    result_msg = await agent.run({
        "problem": req.problem_description,
        "inputs": {}
    })
    
    response = {
        "run_id": run_id,
        "state": result_msg.state, 
        "problem_description": req.problem_description,
        "payload": {
            "trace_log": agent.state.logs,
            "missing_vars": result_msg.payload.get("missing_vars", []),
            "execution_result": result_msg.payload.get("execution_result", {}),
            "code_url": result_msg.payload.get("code_url")
        }
    }
    
    return response

@app.post("/api/run/continue")
async def continue_run(req: RunContinueRequest):
    agent = GlobalOrchestrator(req.run_id)
    
    result_msg = await agent.run({
        "problem": req.problem_description,
        "inputs": req.inputs 
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
        },
        {
            "id": "physics-classical-mechanics-v1",
            "name": "Classical Mechanics",
            "role": "Physicist",
            "icon": "🍎",
            "description": "Solves Newtonian physics problems (forces, motion, energy).",
            "instructions": ["Identify Knowns/Unknowns", "Use Standard Model"],
            "tools": ["formula_db", "solver"],
            "relationships": {"incoming": ["hmao-orchestrator"], "outgoing": []}
        },
        {
            "id": "drone-materials-v1",
            "name": "Materials Agent",
            "role": "Drone Specialist",
            "icon": "🧪",
            "description": "Proposes materials, fasteners, and manufacturing methods.",
            "instructions": ["Check yield strength", "Optimize weight"],
            "tools": ["ashby_charts", "supplier_db"],
            "relationships": {"incoming": ["engineering-core"], "outgoing": ["drone-cad-v1"]}
        },
        {
            "id": "drone-cad-v1",
            "name": "CAD Builder",
            "role": "Design Engineer",
            "icon": "📐",
            "description": "Generates parametric CAD models and drawings.",
            "instructions": ["Maintain parametricity", "Export STEP/STL"],
            "tools": ["opencascade", "freecad"],
            "relationships": {"incoming": ["drone-materials-v1"], "outgoing": ["drone-quick-sim-v1"]}
        },
        {
            "id": "drone-quick-sim-v1",
            "name": "Quick-Sim Agent",
            "role": "Analyst",
            "icon": "🔥",
            "description": "Runs fast sanity checks (FEA/CFD) on designs.",
            "instructions": ["Check max stress", "Verify deflection"],
            "tools": ["sfepy", "calculix"],
            "relationships": {"incoming": ["drone-cad-v1"], "outgoing": []}
        },
        {
            "id": "drone-research-v1",
            "name": "Research Agent",
            "role": "Researcher",
            "icon": "📚",
            "description": "Conducts targeted research on materials and methods.",
            "instructions": ["Find datasheets", "Cite sources"],
            "tools": ["web_search", "knowledge_base"],
            "relationships": {"incoming": ["hmao-orchestrator"], "outgoing": ["drone-materials-v1"]}
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
