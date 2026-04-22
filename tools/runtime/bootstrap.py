import os
import subprocess
import tarfile
import urllib.request

from backend.tools.runtime.contract import CONTRACT


def ensure_solver(solver_name: str):
    """
    JIT loading for physics solvers.
    Pulls binaries from Supabase if not present in the local execution environment.
    """
    solver_dir = f"/tmp/solvers/{solver_name}"
    bin_path = f"{solver_dir}/bin/{solver_name.lower()}"

    if os.path.exists(bin_path):
        return bin_path

    # Get URL from contract
    solver_data = CONTRACT.get("SOLVERS", {}).get(solver_name)
    download_url = solver_data.get("url") if solver_data else None

    if not download_url:
        raise Exception(f"Solver {solver_name} not found in Platform Contract.")

    print(f"JIT: Pulling {solver_name} from Supabase...")
    os.makedirs(solver_dir, exist_ok=True)

    archive_path = f"/tmp/{solver_name}.tar.gz"
    urllib.request.urlretrieve(download_url, archive_path)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=solver_dir)

    os.remove(archive_path)

    # Ensure binary is executable
    subprocess.run(["chmod", "+x", bin_path])
    return bin_path
