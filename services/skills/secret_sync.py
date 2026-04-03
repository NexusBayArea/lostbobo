import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SimHPC-Secrets")

@mcp.tool()
async def sync_production_secrets() -> str:
    """Syncs production secrets from Google Cloud Secret Manager to .env.production."""
    try:
        # Command as specified by the user
        command = 'gcloud secrets versions access latest --secret="PROD_ENV" > .env.production'
        
        # Use shell=True for the redirection
        process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        
        return "Successfully synced production secrets to .env.production."
    except subprocess.CalledProcessError as e:
        return f"Failed to sync secrets: {e.stderr if e.stderr else str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

if __name__ == "__main__":
    mcp.run()
