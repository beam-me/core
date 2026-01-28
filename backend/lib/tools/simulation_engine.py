import sys
import subprocess
import tempfile
import os
import json
from typing import Dict, Any

class SimulationEngineTool:
    """
    Tool for executing Python code in a controlled environment.
    Used by Engineering Core Executor.
    """

    def execute(self, code: str, env_vars: Dict[str, Any]) -> Dict[str, Any]:
        if not code:
            return {"exit_code": -1, "error": "No code provided"}

        # Prepare Environment
        run_env = os.environ.copy()
        
        # Flatten env_vars for passing (BEAM_INPUTS is JSON string)
        if "BEAM_INPUTS" in env_vars:
            if isinstance(env_vars["BEAM_INPUTS"], dict):
                run_env["BEAM_INPUTS"] = json.dumps(env_vars["BEAM_INPUTS"])
            else:
                run_env["BEAM_INPUTS"] = str(env_vars["BEAM_INPUTS"])

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=10,
                env=run_env
            )
            
            os.unlink(tmp_path)
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": None
            }

        except subprocess.TimeoutExpired:
            return {"exit_code": 124, "error": "Execution Timed Out", "stdout": "", "stderr": ""}
        except Exception as e:
            return {"exit_code": 1, "error": str(e), "stdout": "", "stderr": ""}
