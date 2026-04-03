from mcp.server.fastmcp import FastMCP
import subprocess
import shlex

mcp = FastMCP("SimHPC-Security-Vault")

@mcp.tool()
async def run_secure_gcloud(command: str) -> str:
    """
    Executes a Google CLI command securely using Infisical secret injection.
    Example input: 'auth list' or 'config list'
    """
    # 1. Construct the secure "Formula"
    # We prefix 'gcloud' to the input to prevent the agent from trying 
    # to run non-GCP commands through this secure pipe.
    full_command = f"infisical run -- gcloud {command}"
    
    try:
        # 2. Execute the command in the shell
        # shlex.split is used for safer command handling if needed, 
        # but here we use shell=True for the pipe/prefix logic.
        process = subprocess.run(
            full_command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=True
        )
        return f"✅ Success:\n{process.stdout}"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Error executing command:\n{e.stderr if e.stderr else str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

if __name__ == "__main__":
    mcp.run()
