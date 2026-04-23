import subprocess
from pathlib import Path

from backend.tools.runtime.backends.loader import load_asset, set_runtime_env


class MFEMBackend:
    def execute(self, node, context):
        archive = context["assets"]["mfem"]
        root = load_asset("mfem", archive)

        set_runtime_env(root / "lib")

        mesh = node["inputs"]["mesh"]

        binary = root / "bin" / "mfem_solver"
        mesh_path = Path(context["workspace"]) / mesh

        result = subprocess.run([str(binary), str(mesh_path)], capture_output=True, text=True)

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
