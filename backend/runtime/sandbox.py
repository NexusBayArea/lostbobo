import subprocess
import tempfile
import shutil
from pathlib import Path

BASE_IMAGE = "python:3.11-slim"


def run_in_sandbox(script_path: str):
    script_path = Path(script_path).resolve()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # copy repo subset (only what you need)
        workdir = tmp_path / "workspace"
        shutil.copytree(Path.cwd(), workdir)

        # docker run with deterministic environment
        cmd = [
            "docker", "run", "--rm",
            "-e", "RUNTIME_MODE=ci",
            "-e", "PYTHONHASHSEED=0",
            "-v", f"{workdir}:/app",
            "-w", "/app",
            BASE_IMAGE,
            "bash", "-c",
            "pip install -r requirements.lock && python " + script_path.name
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
