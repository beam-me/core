import uuid
import datetime
import os
import sys
from typing import Dict, List, Any, Optional

# Ensure backend directory is in python path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base import BaseAgent, AgentMessage, AgentState

# Import Shared Models
from agents.hmao.models import Task, GlobalState

# Import Cores
from agents.hmao.cores.analysis_core import AnalysisCore
from agents.hmao.cores.engineering_core import EngineeringCore
from agents.drone.propulsion_sizing_agent import PropulsionSizingAgent
from agents.drone.flight_control_safety_agent import FlightControlSafetyAgent
from agents.physics.classical_mechanics_agent import ClassicalMechanicsAgent

# NEW AGENTS
from agents.drone.materials_agent import MaterialsAgent
from agents.drone.cad_agent import CadBuilderAgent
from agents.drone.simulation_agent import QuickSimAgent
from agents.drone.research_agent import ResearchAgent

# Import Modules
from agents.hmao.modules.repository_index import RepositoryIndexModule
from agents.hmao.modules.planner import PlannerModule

# Import Auth
from lib.auth import create_task_token

class GlobalOrchestrator(BaseAgent):
    name = "hmao.orchestrator"
    version = "v1.3.index-aware"

    def __init__(self, run_id: str):
        # FIX: Remove the second argument to match BaseAgent.__init__
        super().__init__(run_id) 
        self.state = GlobalState(run_id=run_id, objective="")
        self.cores = {} 
        
        # Auto-Register Cores
        self.register_core("analysis_core", AnalysisCore(run_id))
        self.register_core("engineering_core", EngineeringCore(run_id))
        self.register_core("engineering-propulsion-v1", PropulsionSizingAgent(run_id))
        self.register_core("engineering-flightcontrol-v1", FlightControlSafetyAgent(run_id))
        self.register_core("physics-classical-mechanics-v1", ClassicalMechanicsAgent(run_id))
        self.register_core("drone-materials-v1", MaterialsAgent(run_id))
        self.register_core("drone-cad-v1", CadBuilderAgent(run_id))
        self.register_core("drone-quick-sim-v1", QuickSimAgent(run_id))
        self.register_core("drone-research-v1", ResearchAgent(run_id))
        
        # Initialize Modules
        self.repo_index = RepositoryIndexModule()
        self.planner = PlannerModule()

    def register_core(self, core_name: str, core_instance: BaseAgent):
        self.cores[core_name] = core_instance

    def log(self, agent: str, step: str, content: str, icon: str = "📡"):
        entry = {
            "agent": agent,
            "step": step,
            "content": content,
            "icon": icon,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.state.logs.append(entry)
        return entry

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method if called directly via base class, but Orchestrator manages its own flow in run()"""
        return {}
        
    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method"""
        return {}

    async def run(self, input_payload: Dict[str, Any]) -> AgentMessage:
        problem = input_payload.get("problem", "")
        user_inputs = input_payload.get("inputs", {})
        
        self.state.objective = problem
        self.state.artifacts["inputs"] = user_inputs
        
        # 1. Intake Phase
        self.log("Orchestrator", "Intake", f"Objective received: {problem}", "📡")

        # 2. Repository Lookup & Strategy
        self.log("Orchestrator", "Index", "Querying Repository Index for existing solutions...", "🔍")
        
        try:
            matches = self.repo_index.lookup(problem, limit=1)
        except Exception as e:
            self.log("Orchestrator", "Warning", f"Index lookup failed: {e}", "⚠️")
            matches = []
        
        strategy = "BUILD"
        reuse_artifact = None
        
        if matches:
            best_match = matches[0]
            similarity = best_match.get("similarity_score", 0)
            
            if similarity > 0.90:
                strategy = "REUSE"
                reuse_artifact = best_match
                self.log("Orchestrator", "Strategy", f"Exact match found (Score: {similarity:.2f}). Strategy: REUSE.", "⚡️")
                self.log("Orchestrator", "Info", f"Reusing artifact: {best_match.get('artifact_id')}", "📂")
            elif similarity > 0.75:
                strategy = "MODIFY"
                reuse_artifact = best_match
                self.log("Orchestrator", "Strategy", f"Similar project found (Score: {similarity:.2f}). Strategy: MODIFY.", "🔧")
                self.log("Orchestrator", "Info", f"Basing design on: {best_match.get('artifact_id')}", "📂")
            else:
                self.log("Orchestrator", "Strategy", f"Low similarity ({similarity:.2f}). Starting fresh build.", "🧱")
        else:
            self.log("Orchestrator", "Strategy", "No previous projects found. Starting fresh build.", "🧱")

        # 3. Decomposition (Delegated to Planner)
        try:
            # FIX: Passed 'strategy' and 'reuse_artifact' to generate_plan
            self.state.tasks = self.planner.generate_plan(
                problem, 
                strategy=strategy, 
                reuse_artifact=reuse_artifact
            )
            self.log("Orchestrator", "Decomposition", f"DAG constructed with {len(self.state.tasks)} tasks.", "🔀")
        except Exception as e:
            self.log("Orchestrator", "Error", f"Planning failed: {e}", "❌")
            # FIX: Use keyword arguments for AgentMessage
            return AgentMessage(
                run_id=self.run_id, 
                from_agent=self.name, 
                state=AgentState.FAILED, 
                summary=f"Planning Error: {e}", 
                confidence=0.0
            )

        # 4. Execution Loop
        max_loops = 15
        loop_count = 0
        mission_success = False
        
        while loop_count < max_loops:
            loop_count += 1
            all_complete = True
            progress_made = False
            
            # Check tasks
            # Rebuild list each iteration as tasks update
            # Sort by dependency resolution
            
            pending_tasks = []
            for t_id, task in self.state.tasks.items():
                if task.status not in ["COMPLETED", "FAILED", "SKIPPED"]:
                    pending_tasks.append(task)
            
            if not pending_tasks:
                mission_success = True
                break
            
            any_dispatch = False
            
            for task in pending_tasks:
                # Check dependencies
                deps_met = True
                for dep in task.dependencies:
                    if dep in self.state.tasks:
                         if self.state.tasks[dep].status not in ["COMPLETED", "SKIPPED"]:
                             deps_met = False
                             break
                
                if deps_met:
                    any_dispatch = True
                    all_complete = False
                    
                    self.log("Orchestrator", "Dispatch", f"Dispatching {task.id} to {task.assigned_core}", "🚀")
                    
                    core = self.cores.get(task.assigned_core)
                    if not core:
                        self.log("Orchestrator", "Error", f"Core {task.assigned_core} not found! Skipping task.", "⚠️")
                        task.status = "SKIPPED"
                        continue

                    # Context Injection
                    context = {
                        "objective": self.state.objective,
                        "task": task.description,
                        "artifacts": self.state.artifacts,
                        "inputs": user_inputs,
                        "metadata": task.metadata, 
                    }

                    try:
                        # We need to await the run call
                        # The BaseAgent.run is async
                        result_msg = await core.run(context)
                        
                        if result_msg.state == AgentState.COMPLETED:
                            task.result = result_msg.payload
                            task.status = "COMPLETED"
                            progress_made = True
                            
                            if isinstance(result_msg.payload, dict):
                                if "trace_log" in result_msg.payload:
                                    # Filter logs to avoid duplication if possible
                                    new_logs = result_msg.payload["trace_log"]
                                    self.state.logs.extend(new_logs)
                            
                                # Merge outputs into artifacts
                                for k, v in result_msg.payload.items():
                                    if k not in ["trace_log", "execution_result", "code_url"]:
                                        self.state.artifacts[k] = v
                                        
                                if "code_url" in result_msg.payload:
                                    self.state.artifacts["code_url"] = result_msg.payload["code_url"]
                                if "execution_result" in result_msg.payload:
                                    self.state.artifacts["execution_result"] = result_msg.payload["execution_result"]
                            
                            self.log("Orchestrator", "Reconciliation", f"Task {task.id} completed.", "✅")
                        
                        # NEW: Handle AWAITING_USER
                        elif result_msg.state == AgentState.AWAITING_USER:
                            self.log("Orchestrator", "Pause", f"Task {task.id} requires user input.", "🙋")
                            if isinstance(result_msg.payload, dict) and "trace_log" in result_msg.payload:
                                self.state.logs.extend(result_msg.payload["trace_log"])
                            
                            # Return immediately to prompt user
                            return AgentMessage(
                                run_id=self.run_id,
                                from_agent=self.name,
                                state=AgentState.AWAITING_USER,
                                summary="User Input Required",
                                confidence=1.0,
                                payload={
                                    "missing_vars": result_msg.payload.get("missing_vars", []),
                                    "trace_log": self.state.logs
                                }
                            )

                        else:
                            task.status = "FAILED"
                            self.log("Orchestrator", "Failure", f"Task {task.id} failed: {result_msg.summary}", "💥")
                            
                    except Exception as e:
                        task.status = "FAILED"
                        self.log("Orchestrator", "Crash", f"Task {task.id} crashed: {e}", "🔥")
            
            if not progress_made and pending_tasks:
                if not any_dispatch:
                     self.log("Orchestrator", "Deadlock", "Circular dependency or missing tasks detected.", "🛑")
                else:
                     self.log("Orchestrator", "Pause", "Tasks are running (in theory parallel), waiting...", "⏳")
                     # In a real async system we'd wait, but here we run sequentially so if no progress made it's over
                break

        # 5. Indexing Phase (NEW)
        if mission_success:
            self.log("Orchestrator", "Indexing", "Run successful. Indexing results for future reuse...", "💾")
            try:
                # Prepare metadata
                meta = {
                    "completed_at": datetime.datetime.now().isoformat(),
                    "tasks_count": len(self.state.tasks),
                    "code_url": self.state.artifacts.get("code_url")
                }
                
                success = self.repo_index.index_run(
                    run_id=self.run_id,
                    problem=self.state.objective,
                    code_url=self.state.artifacts.get("code_url"),
                    metadata=meta
                )
                if success:
                    self.log("Orchestrator", "Indexing", "Run indexed successfully.", "✅")
                else:
                    self.log("Orchestrator", "Warning", "Failed to index run.", "⚠️")
            except Exception as e:
                 self.log("Orchestrator", "Error", f"Indexing crashed: {e}", "❌")
                
        # 6. Final Freeze
        return AgentMessage(
            run_id=self.run_id,
            from_agent=self.name,
            state=AgentState.COMPLETED,
            summary="Mission Accomplished",
            confidence=1.0,
            payload={
                "trace_log": self.state.logs,
                "artifacts": self.state.artifacts,
                "execution_result": self.state.artifacts.get("execution_result"),
                "code_url": self.state.artifacts.get("code_url")
            }
        )
