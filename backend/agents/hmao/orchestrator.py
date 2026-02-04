import uuid
import datetime
from typing import Dict, List, Any, Optional

# ABSOLUTE IMPORT FIX
from agents.base import BaseAgent, AgentMessage, AgentState

# Import Shared Models
from agents.hmao.models import Task, GlobalState

# Import Cores (Absolute)
from agents.hmao.cores.analysis_core import AnalysisCore
from agents.hmao.cores.engineering_core import EngineeringCore
from agents.drone.propulsion_sizing_agent import PropulsionSizingAgent
from agents.drone.flight_control_safety_agent import FlightControlSafetyAgent

# Import Modules (Absolute)
from agents.hmao.modules.repository_index import RepositoryIndexModule
from agents.hmao.modules.planner import PlannerModule

# Import Auth
from lib.auth import create_task_token

class GlobalOrchestrator(BaseAgent):
    name = "hmao.orchestrator"
    version = "v1.2.refactor"

    def __init__(self, run_id: str):
        super().__init__(run_id)
        self.state = GlobalState(run_id=run_id, objective="")
        self.cores = {} 
        
        # Auto-Register Cores
        self.register_core("analysis_core", AnalysisCore(run_id))
        self.register_core("engineering_core", EngineeringCore(run_id))
        self.register_core("engineering-propulsion-v1", PropulsionSizingAgent(run_id))
        self.register_core("engineering-flightcontrol-v1", FlightControlSafetyAgent(run_id))
        
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

    async def run(self, input_payload: Dict[str, Any]) -> AgentMessage:
        problem = input_payload.get("problem", "")
        user_inputs = input_payload.get("inputs", {})
        
        self.state.objective = problem
        
        if user_inputs:
            self.state.artifacts["variables"] = user_inputs
        
        # 1. Intake Phase
        self.log("Orchestrator", "Intake", f"Objective received: {problem}", "📡")

        # 2. Repository Lookup & Strategy
        self.log("Orchestrator", "Index", "Querying Repository Index for existing solutions...", "🔍")
        matches = self.repo_index.lookup(problem, limit=1)
        
        strategy = "BUILD"
        reuse_artifact = None
        
        if matches:
            best_match = matches[0]
            similarity = best_match["similarity_score"]
            if similarity > 0.92:
                strategy = "REUSE"
                reuse_artifact = best_match
                self.log("Orchestrator", "Strategy", f"Exact match found (Score: {similarity:.2f}). Strategy: REUSE.", "⚡️")
            elif similarity > 0.75:
                strategy = "MODIFY"
                reuse_artifact = best_match
                self.log("Orchestrator", "Strategy", f"Partial match found (Score: {similarity:.2f}). Strategy: MODIFY.", "🔧")
            else:
                self.log("Orchestrator", "Strategy", f"Low similarity ({similarity:.2f}). Strategy: BUILD.", "🧱")
        else:
            self.log("Orchestrator", "Strategy", "No matches found. Strategy: BUILD.", "🧱")

        # 3. Decomposition (Delegated to Planner)
        self.state.tasks = self.planner.generate_plan(problem, strategy, reuse_artifact)
        self.log("Orchestrator", "Decomposition", f"DAG constructed with {len(self.state.tasks)} tasks.", "🔀")

        # 4. Execution Loop
        max_loops = 10
        loop_count = 0
        
        while loop_count < max_loops:
            loop_count += 1
            all_complete = True
            progress_made = False
            
            for task_id, task in self.state.tasks.items():
                if task.status == "COMPLETED":
                    continue
                
                all_complete = False
                
                if not all(self.state.tasks[dep].status == "COMPLETED" for dep in task.dependencies):
                    continue

                self.log("Orchestrator", "Dispatch", f"Dispatching {task.id} to {task.assigned_core}", "🚀")
                
                core = self.cores.get(task.assigned_core)
                if not core:
                    return AgentMessage(
                        run_id=self.run_id, 
                        from_agent=self.name, 
                        state=AgentState.FAILED, 
                        summary="Core not found",
                        confidence=0.0
                    )

                # Mint Task Token
                task_token = create_task_token(
                    task_id=task.id,
                    cores=[task.assigned_core],
                    allow_direct=True
                )

                # Context Injection
                context = {
                    "objective": self.state.objective,
                    "task": task.description,
                    "artifacts": self.state.artifacts,
                    "inputs": user_inputs,
                    "metadata": task.metadata, # Pass reuse metadata (mode, artifact)
                    "task_token": task_token # <--- PASSED HERE
                }

                result_msg = await core.run(context)

                if result_msg.state == AgentState.COMPLETED:
                    task.result = result_msg.payload
                    task.status = "COMPLETED"
                    progress_made = True
                    
                    if "trace_log" in result_msg.payload:
                        self.state.logs.extend(result_msg.payload["trace_log"])
                    
                    if "variables" in result_msg.payload:
                        if user_inputs:
                             result_msg.payload["variables"].update(user_inputs)
                        self.state.artifacts["variables"] = result_msg.payload["variables"]
                        
                    if "code_url" in result_msg.payload:
                        self.state.artifacts["code_url"] = result_msg.payload["code_url"]
                    if "execution_result" in result_msg.payload:
                        self.state.artifacts["execution_result"] = result_msg.payload["execution_result"]
                    
                    if "missing_vars" in result_msg.payload:
                        self.log("Orchestrator", "Pause", "Clarification needed from user.", "🙋")
                        return AgentMessage(
                            run_id=self.run_id,
                            from_agent=self.name,
                            state=AgentState.AWAITING_USER,
                            summary="Clarification Needed",
                            confidence=1.0, 
                            payload={
                                "missing_vars": result_msg.payload["missing_vars"],
                                "trace_log": self.state.logs
                            }
                        )
                    
                    self.log("Orchestrator", "Reconciliation", f"Task {task.id} completed successfully.", "✅")
                else:
                    task.status = "FAILED"
                    self.log("Orchestrator", "Failure", f"Task {task.id} failed: {result_msg.summary}", "💥")
                    return result_msg
            
            if all_complete:
                break
                
        # 5. Final Freeze
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
