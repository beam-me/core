import datetime
from typing import Dict, List, Any
from abc import ABC, abstractmethod
# ABSOLUTE IMPORT FIX
from agents.base import BaseAgent, AgentMessage, AgentState

class DisciplineCore(BaseAgent, ABC):
    """
    HMAO Discipline Core.
    Enforces the Triad Pattern: Planner -> Executor -> Critic.
    """
    
    def __init__(self, run_id: str, name: str):
        super().__init__(run_id)
        self.core_name = name
        self.trace_log = []

    def log(self, role: str, step: str, content: str, icon: str = "🔹"):
        self.trace_log.append({
            "agent": f"{self.core_name}.{role}",
            "step": step,
            "content": content,
            "icon": icon,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def run(self, context: Dict[str, Any]) -> AgentMessage:
        self.trace_log = [] # Reset log for this run
        self.log("System", "Boot", "Core Initialized. Loading Context...", "🔋")

        try:
            # 1. PLANNER
            self.log("Planner", "Analysis", "Interpreting Orchestrator Requirements...", "📋")
            plan = await self._plan(context)
            self.log("Planner", "Strategy", f"Execution Plan: {plan.get('summary')}", "📐")

            # 2. EXECUTOR
            self.log("Executor", "Action", "Engaging Toolchain...", "🛠️")
            execution_result = await self._execute(plan, context)
            self.log("Executor", "Output", "Task Execution Complete.", "📦")

            # 3. CRITIC
            self.log("Critic", "Review", "Running Deterministic Validation...", "🧐")
            validation = await self._validate(execution_result, context)
            
            if validation.get("passed", False):
                self.log("Critic", "Approval", "Result Validated. Promoting to Orchestrator.", "✅")
                return AgentMessage(
                    run_id=self.run_id,
                    from_agent=self.core_name,
                    state=AgentState.COMPLETED,
                    summary="Core Execution Successful",
                    confidence=1.0, # FIXED: Added confidence
                    payload={
                        **execution_result,
                        "trace_log": self.trace_log
                    }
                )
            else:
                self.log("Critic", "Rejection", f"Validation Failed: {validation.get('reason')}", "❌")
                return AgentMessage(
                    run_id=self.run_id,
                    from_agent=self.core_name,
                    state=AgentState.FAILED,
                    summary=f"Validation Failed: {validation.get('reason')}",
                    confidence=0.0, # FIXED: Added confidence
                    payload={"trace_log": self.trace_log}
                )

        except Exception as e:
            self.log("System", "Crash", f"Core Exception: {str(e)}", "💀")
            return AgentMessage(
                run_id=self.run_id,
                from_agent=self.core_name,
                state=AgentState.FAILED,
                summary=str(e),
                confidence=0.0, # FIXED: Added confidence
                payload={"trace_log": self.trace_log}
            )

    @abstractmethod
    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Role: Lead Planner"""
        pass

    @abstractmethod
    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Role: Tool-Augmented Executor"""
        pass

    @abstractmethod
    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Role: Validation Critic"""
        pass
