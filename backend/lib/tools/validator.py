import sys
import subprocess
import tempfile
import os
import json
from typing import Dict, Any

class ValidatorTool:
    """
    Tool for deterministic validation of engineering code.
    Used by Engineering Core Critic.
    """

    def validate_robustness(self, code: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the code with stringified inputs to test type safety.
        """
        if not code:
            return {"passed": False, "reason": "No code provided"}

        # FUZZING: Convert all inputs to strings
        stringified_vars = {k: str(v) for k, v in variables.items()}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            run_env = os.environ.copy()
            run_env["BEAM_INPUTS"] = json.dumps(stringified_vars)

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=5,
                env=run_env
            )
            
            os.unlink(tmp_path)

            if result.returncode != 0:
                return {
                    "passed": False, 
                    "reason": f"Crash on String Inputs (Exit {result.returncode}). Did you cast float()?",
                    "stderr": result.stderr
                }
            
            if "Calculated Result:" not in result.stdout:
                return {
                    "passed": False,
                    "reason": "Output missing 'Calculated Result:'"
                }

            return {"passed": True}

        except Exception as e:
            return {"passed": False, "reason": f"Validator Error: {str(e)}"}
