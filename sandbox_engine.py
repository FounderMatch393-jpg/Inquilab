import os
import subprocess
import sys
import tempfile

class SecureSandbox:
    """Execute agent-provided Python code in a short-lived local process."""

    def _execute_locally(self, code: str, timeout: int = 15) -> str:
        """Execute code locally with captured output and a time limit."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            script_path = temp_file.name

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            output = (result.stdout or "") + (result.stderr or "")
            if result.returncode == 0:
                return f"Observation: Local Python execution successful.\nOutput:\n{output}"
            return f"Observation: Local Python execution failed with exit code {result.returncode}.\nError:\n{output}"
        except subprocess.TimeoutExpired:
            return (
                f"Observation: Local Python execution timed out after {timeout}s.\n"
                "Please keep scripts short and avoid long-running loops."
            )
        except Exception as exc:
            return f"Observation: Local Python fallback failed.\nDetails: {exc}"
        finally:
            try:
                os.unlink(script_path)
            except Exception:
                pass

    def execute_code(self, code: str, timeout: int = 15) -> str:
        """Execute Python code in a short-lived local process."""
        return self._execute_locally(code, timeout=timeout)
