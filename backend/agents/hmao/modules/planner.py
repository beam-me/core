from typing import List, Dict, Any, Optional
from agents.hmao.models import Task
from lib.llm import call_llm
import json
import os

class PlannerModule:
    """
    Decides the strategy and generates the task DAG based on the problem and context.
    Uses an LLM and external prompt for decision making.
    """
    
    def __init__(self):
        # Path logic: agents/hmao/modules/../../../prompts
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.prompt_path = os.path.join(base_dir, "prompts", "orchestrator_planner.md")

    def generate_plan(self, problem: str, strategy: str, reuse_artifact: Optional[Dict[str, Any]] = None) -> Dict[str, Task]:
        
        # 1. Load Prompt
        try:
            with open(self.prompt_path, "r") as f:
                raw_prompt = f.read()
        except Exception as e:
            # Fallback to hardcoded if file missing (Safety)
            print(f"Error loading planner prompt: {e}")
            return self._fallback_plan(problem, strategy, reuse_artifact)

        # 2. Prepare Context
        artifact_desc = "None"
        if reuse_artifact:
            artifact_desc = f"File: {reuse_artifact.get('file_path')}, Desc: {reuse_artifact.get('problem_description')}"
            
        system_prompt = raw_prompt.replace("{{strategy}}", strategy)
        system_prompt = system_prompt.replace("{{reuse_artifact_desc}}", artifact_desc)
        
        user_prompt = f"Problem: {problem}"
        
        # 3. Call LLM (JSON MODE)
        response = call_llm(system_prompt, user_prompt, json_mode=True)
        
        if not response:
            return self._fallback_plan(problem, strategy, reuse_artifact)
            
        # 4. Parse Response
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            plan_data = json.loads(cleaned)
            tasks_list = plan_data.get("tasks", [])
            
            tasks_dict = {}
            for t in tasks_list:
                # Hydrate Metadata with actual object if needed
                meta = t.get("metadata", {})
                if reuse_artifact and meta.get("mode") in ["REUSE", "MODIFY"]:
                    meta["artifact"] = reuse_artifact
                    
                task_obj = Task(
                    id=t["id"],
                    description=t["description"],
                    assigned_core=t["assigned_core"],
                    dependencies=t.get("dependencies", []),
                    metadata=meta
                )
                tasks_dict[task_obj.id] = task_obj
                
            return tasks_dict
            
        except Exception as e:
            print(f"Planner Parsing Error: {e}")
            return self._fallback_plan(problem, strategy, reuse_artifact)

    def _fallback_plan(self, problem: str, strategy: str, reuse_artifact: Optional[Dict[str, Any]]) -> Dict[str, Task]:
        """
        Original hardcoded logic as a safety fallback.
        """
        tasks: Dict[str, Task] = {}

        if "drone" in problem.lower() or "quadcopter" in problem.lower() or "uav" in problem.lower():
            task1 = Task(
                id="task_propulsion",
                description="Select propulsion system based on requirements.",
                assigned_core="engineering-propulsion-v1"
            )
            task2 = Task(
                id="task_safety_check",
                description="Validate propulsion configuration for flight stability.",
                assigned_core="engineering-flightcontrol-v1",
                dependencies=["task_propulsion"]
            )
            tasks = {task1.id: task1, task2.id: task2}
            
        elif strategy == "REUSE" and reuse_artifact:
            task1 = Task(
                id="task_analyze_reuse",
                description=f"Analyze inputs for existing solution: {reuse_artifact.get('file_path')}",
                assigned_core="analysis_core"
            )
            task2 = Task(
                id="task_execute_reuse",
                description="Execute existing solution.",
                assigned_core="engineering_core",
                dependencies=["task_analyze_reuse"],
                metadata={"mode": "REUSE", "artifact": reuse_artifact}
            )
            tasks = {task1.id: task1, task2.id: task2}

        elif strategy == "MODIFY" and reuse_artifact:
            task1 = Task(
                id="task_analyze_diff",
                description=f"Analyze requirements diff.",
                assigned_core="analysis_core"
            )
            task2 = Task(
                id="task_modify_run",
                description=f"Refactor {reuse_artifact.get('file_path')} to meet new requirements.",
                assigned_core="engineering_core",
                dependencies=["task_analyze_diff"],
                metadata={"mode": "MODIFY", "artifact": reuse_artifact}
            )
            tasks = {task1.id: task1, task2.id: task2}

        else:
            task1 = Task(
                id="task_analyze",
                description=f"Analyze requirements for: {problem}",
                assigned_core="analysis_core"
            )
            task2 = Task(
                id="task_implement",
                description="Implement the solution based on analysis.",
                assigned_core="engineering_core",
                dependencies=["task_analyze"]
            )
            tasks = {task1.id: task1, task2.id: task2}

        return tasks
