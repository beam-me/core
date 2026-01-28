from typing import Dict, Any
# ABSOLUTE IMPORT FIX
from agents.hmao.core import DisciplineCore

# IMPORT TOOLS
from lib.tools.code_generator import CodeGeneratorTool
from lib.tools.simulation_engine import SimulationEngineTool
from lib.tools.validator import ValidatorTool
from lib.tools.github_client import GitHubTool

class EngineeringCore(DisciplineCore):
    """
    Core ID: engineering_core
    Responsibility: Code Generation, Execution, and Validation
    """
    def __init__(self, run_id: str):
        super().__init__(run_id, "engineering_core")
        # Tools
        self.generator = CodeGeneratorTool()
        self.simulator = SimulationEngineTool()
        self.validator = ValidatorTool()
        self.github = GitHubTool()

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
            
            # Run Once (Assuming trusted artifact is robust, but still good to run)
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
                        plan=context.get("task"),
                        variables=variables,
                        previous_code=current_code, # Used for Modify
                        error_feedback=None
                    )
                else:
                    self.log("Executor", "Refinement", f"Attempt {attempt+1}: Fixing errors...", "🩹")
                    current_code = self.generator.generate(
                        problem=context.get("objective"),
                        plan="Fix the code based on error.",
                        variables=variables,
                        previous_code=current_code,
                        error_feedback=error_feedback
                    )

                # 2. Simulate (Functionality Check)
                exec_result = self.simulator.execute(current_code, {"BEAM_INPUTS": variables})
                if exec_result["exit_code"] != 0:
                    error_feedback = f"Runtime Error: {exec_result['stderr'] or exec_result['error']}"
                    self.log("Executor", "Check", f"Simulation Failed: {error_feedback}", "❌")
                    continue # Loop back to fix

                # 3. Validate Robustness (Fuzzing Check)
                # We do this INSIDE the loop so the generator learns to cast types.
                robust_res = self.validator.validate_robustness(current_code, variables)
                if not robust_res["passed"]:
                    error_feedback = f"Robustness Error (Input Fuzzing): {robust_res['reason']}. \nHINT: Did you forget to float() cast the inputs?"
                    self.log("Executor", "Check", f"Robustness Failed: {robust_res['reason']}", "🛡️❌")
                    continue # Loop back to fix

                # If we get here, both passed
                self.log("Executor", "Success", "Code passed all internal checks.", "✅")
                generated_code = current_code
                break

            # Check if we exited loop without success
            if not generated_code and error_feedback:
                self.log("Executor", "GiveUp", "Max retries reached. Returning last attempt.", "🏳️")
                # We return whatever we have, Validation Critic will reject it officially
                generated_code = current_code 

            # Push Code if success (or best effort)
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
        # 1. Check Execution Result
        exec_res = result.get("execution_result", {})
        if exec_res.get("exit_code") != 0:
            return {"passed": False, "reason": f"Runtime Error: {exec_res.get('error') or exec_res.get('stderr')}"}
        
        # 2. Run Deterministic Robustness Check (Fuzzing)
        code = result.get("generated_code")
        variables = result.get("variables")
        
        validation = self.validator.validate_robustness(code, variables)
        if not validation["passed"]:
            return validation
            
        return {"passed": True}
