import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SimHPC-Deployment-Guardian")

def run_command(cmd, shell=True):
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    return result

@mcp.tool()
async def safe_deploy_gcp(service_name: str) -> str:
    """
    The ultimate safety gate. Lints code, then deploys to GCP using Infisical.
    Target: 'api' or 'worker'
    """
    # Step 1: Ruff Audit
    # Using python -m ruff to ensure it uses the environment's ruff
    lint = run_command("python -m ruff check services/api/api.py services/worker/worker.py")
    
    if lint.returncode != 0:
        return f"❌ Deployment Aborted: Linting failed.\n{lint.stdout}\n{lint.stderr}"

    # Step 2: Infisical + GCloud Handshake
    # This uses the formula: infisical run -- [command]
    # Note: Using --quiet to prevent interactive prompts during deployment
    deploy_cmd = f"infisical run -- gcloud app deploy --project=simhpc-alpha --service={service_name} --quiet"
    
    deploy = run_command(deploy_cmd)
    
    if deploy.returncode == 0:
        return f"✅ Deployment Successful!\n{deploy.stdout}"
    else:
        return f"❌ GCP Deployment Error:\n{deploy.stderr}"

if __name__ == "__main__":
    mcp.run()
