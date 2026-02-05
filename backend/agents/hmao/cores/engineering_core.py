from typing import Dict, Any
# ABSOLUTE IMPORT FIX
from agents.hmao.core import DisciplineCore

# IMPORT TOOLS
from lib.tools.code_generator import CodeGeneratorTool
from lib.tools.simulation_engine import SimulationEngineTool
from lib.tools.validator import ValidatorTool
from lib.tools.github_client import GitHubTool
from lib.abn_client import ABNClient
from lib.knowledge_base import KnowledgeBase
import json
import os

class EngineeringCore(DisciplineCore):
    """
    Core ID: engineering_core
    Responsibility: Code Generation, Execution, and Validation.
    Has access to Best Practices KB.
    """
    name = "engineering_core"
    
    def __init__(self, run_id: str):
        super().__init__(run_id, "engineering_core")
        # Tools
        self.generator = CodeGeneratorTool()
        self.simulator = SimulationEngineTool()
        self.validator = ValidatorTool()
        self.github = GitHubTool()
        
        # Initialize Knowledge Base
        # Path logic: backend/agents/hmao/cores/engineering_core.py -> backend/knowledge
        # Needs 4 dirnames
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        kb_path = os.path.join(base_dir, "knowledge", "engineering_best_practices.json")
        self.kb = KnowledgeBase(kb_path)

    async def _plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        metadata = context.get("metadata", {})
        mode = metadata.get("mode", "BUILD")
        
        return {
            "summary": f"Execute Engineering Task in {mode} mode.",
            "filename": f"solutions/{self.run_id}/main.py",
            "mode": mode,
            "artifact": metadata.get("artifact")
        }

    async def _execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        variables = context.get("artifacts", {}).get("variables", {})
        mode = plan.get("mode")
        filename = plan.get("filename")
        
        # Retrieve Knowledge
        conventions = self.kb.search("python_conventions")
        patterns = self.kb.search("physics_patterns")
        
        kb_context = f"""
        Engineering Best Practices:
        Python: {json.dumps(conventions, indent=2)}
        Physics: {json.dumps(patterns, indent=2)}
        """
        
        # Inject KB into the plan description for the Generator
        enhanced_plan_desc = f"{context.get('task')}\n\nSTRICTLY FOLLOW THESE BEST PRACTICES:\n{kb_context}"
        
        generated_code = ""
        code_url = ""
        exec_result = {}

        # --- STRATEGY: REUSE ---
        if mode == "REUSE":
            artifact = plan.get("artifact")
            file_path = artifact.get("file_path")
            self.log("Executor", "Retrieval", f"Fetching verified code from {file_path}...", "📥")
            
            generated_code = self.github.fetch_code(file_path)
            code_url = f"https://github.com/beam-me/user-code/blob/main/{file_path}"
            
            # Run Once
            exec_result = self.simulator.execute(generated_code, {"BEAM_INPUTS": variables})

        # --- STRATEGY: BUILD / MODIFY ---
        else:
            previous_code = None
            if mode == "MODIFY":
                artifact = plan.get("artifact")
                file_path = artifact.get("file_path")
                previous_code = self.github.fetch_code(file_path)
                self.log("Executor", "Refactor", f"Refactoring {file_path}...", "🔧")

            # Self-Healing Loop
            max_retries = 3
            current_code = previous_code
            error_feedback = None

            for attempt in range(max_retries):
                # 1. Generate
                if attempt == 0 and not error_feedback:
                    current_code = self.generator.generate(
                        problem=context.get("objective"),
                        plan=enhanced_plan_desc, # <--- INJECTED HERE
                        variables=variables,
                        previous_code=current_code, 
                        error_feedback=None
                    )
                else:
                    self.log("Executor", "Refinement", f"Attempt {attempt+1}: Fixing errors...", "🩹")
                    current_code = self.generator.generate(
                        problem=context.get("objective"),
                        plan=enhanced_plan_desc,
                        variables=variables,
                        previous_code=current_code,
                        error_feedback=error_feedback
                    )

                # 2. Simulate
                exec_result = self.simulator.execute(current_code, {"BEAM_INPUTS": variables})
                if exec_result["exit_code"] != 0:
                    error_feedback = f"Runtime Error: {exec_result['stderr'] or exec_result['error']}"
                    self.log("Executor", "Check", f"Simulation Failed: {error_feedback}", "❌")
                    continue 

                # 3. Validate Robustness
                robust_res = self.validator.validate_robustness(current_code, variables)
                if not robust_res["passed"]:
                    error_feedback = f"Robustness Error: {robust_res['reason']}. \nHINT: Did you forget to float() cast the inputs?"
                    self.log("Executor", "Check", f"Robustness Failed: {robust_res['reason']}", "🛡️❌")
                    continue

                # If we get here, both passed
                self.log("Executor", "Success", "Code passed all internal checks.", "✅")
                generated_code = current_code
                break

            if not generated_code and error_feedback:
                self.log("Executor", "GiveUp", "Max retries reached. Returning last attempt.", "🏳️")
                generated_code = current_code 

            # --- ABN STEP: CODE REVIEW ---
            if generated_code:
                try:
                    self.log("Orchestrator", "Request", "Requesting QA Code Review...", "📡")
                    # Use ABN if available
                    if self.abn:
                        abn = self.abn
                    else:
                        abn = ABNClient(self.name, "legacy")

                    target_id = await abn.request_connection("Perform code review and security check")
                    
                    if target_id:
                        self.log("ABN", "Propose", f"Sending code to {target_id}...", "📤")
                        review = await abn.send_message(target_id, "REVIEW_REQUEST", {"code": generated_code})
                        
                        if review:
                            status = review.get("status", "UNKNOWN")
                            score = review.get("score", 0)
                            self.log("ABN", "Receive", f"QA Review: {status} (Score: {score}/100)", "📥")
                            if status == "REJECTED":
                                self.log("Executor", "Warning", "QA Rejected the code. Proceeding with caution.", "⚠️")
                except Exception as e:
                    self.log("ABN", "Error", f"QA Negotiation failed: {e}", "⚠️")

            # Push Code
            if generated_code:
                msg = f"feat: solution for {self.run_id}"
                try:
                    code_url = self.github.push_code(filename, generated_code, msg)
                except Exception as e:
                    self.log("Executor", "PushFail", f"Failed to push code: {e}", "⚠️")
                    code_url = "http://failed-to-push"
            else:
                 raise Exception("Failed to generate working code after retries.")

        return {
            "code_url": code_url,
            "generated_code": generated_code,
            "execution_result": exec_result,
            "variables": variables
        }

    async def _validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        exec_res = result.get("execution_result", {})
        if exec_res.get("exit_code") != 0:
            return {"passed": False, "reason": f"Runtime Error: {exec_res.get('error') or exec_res.get('stderr')}"}
        
        code = result.get("generated_code")
        variables = result.get("variables")
        
        validation = self.validator.validate_robustness(code, variables)
        if not validation["passed"]:
            return validation
            
        return {"passed": True}
