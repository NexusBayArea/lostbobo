import os
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP
from supabase import create_client
from dotenv import load_dotenv

# Load .env for local testing if needed, though MCP usually provides these
load_dotenv()

mcp = FastMCP("SimHPC-Resource-Reaper")

# Initialize Supabase (using Service Role for admin access)
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    # We'll defer erroring until the tool is actually called to allow server to start
    supabase = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

@mcp.tool()
async def reap_idle_workers() -> str:
    """
    Identifies and terminates RunPod instances that have stopped sending heartbeats.
    Prevents 'Zombie' GPU costs.
    """
    if not supabase:
        return "❌ Error: Supabase credentials (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) are missing from the environment."
    
    if not RUNPOD_API_KEY:
        return "❌ Error: RUNPOD_API_KEY is missing from the environment."

    reaped_count = 0
    logs = []

    try:
        # 1. Get all active pods from RunPod
        async with httpx.AsyncClient() as client:
            # RunPod GraphQL API call to get user pods
            query = {"query": "{ myself { pods { id name status } } }"}
            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            response = await client.post("https://api.runpod.io/graphql", json=query, headers=headers)
            
            if response.status_code != 200:
                return f"❌ Error fetching pods from RunPod: {response.text}"
                
            data = response.json()
            if 'errors' in data:
                return f"❌ RunPod API Error: {data['errors']}"
                
            pods = data['data']['myself']['pods']

            for pod in pods:
                pod_id = pod['id']
                
                # 2. Check last heartbeat in Supabase
                res = supabase.table("worker_heartbeat").select("last_ping").eq("pod_id", pod_id).single().execute()
                
                if not res.data:
                    logs.append(f"⚠️ Pod {pod_id} has no heartbeat record in Supabase. Flagging for review.")
                    continue

                # Parse the ISO timestamp and ensure it's timezone-aware
                last_ping_str = res.data['last_ping'].replace('Z', '+00:00')
                last_ping = datetime.fromisoformat(last_ping_str)
                
                # Use current UTC time for comparison
                now = datetime.now(timezone.utc)
                is_stale = now - last_ping > timedelta(minutes=15)

                # 3. Reap if stale and currently 'RUNNING'
                if is_stale and pod['status'] == 'RUNNING':
                    # Termination API Call
                    terminate_query = {"query": f"mutation {{ terminatePod(input: {{ podId: \"{pod_id}\" }}) }}"}
                    term_resp = await client.post("https://api.runpod.io/graphql", json=terminate_query, headers=headers)
                    
                    if term_resp.status_code == 200:
                        reaped_count += 1
                        logs.append(f"💀 Reaped stale Pod {pod_id} (Last heartbeat: {last_ping.strftime('%H:%M:%S')} UTC)")
                    else:
                        logs.append(f"❌ Failed to terminate Pod {pod_id}: {term_resp.text}")

        if reaped_count == 0:
            status_msg = "✅ Fleet Check Complete: All active workers are healthy and heartbeating."
            if logs:
                return f"{status_msg}\n\nNotes:\n" + "\n".join(logs)
            return status_msg
        
        return f"🛠️ Cleanup Complete:\n" + "\n".join(logs)

    except Exception as e:
        return f"❌ An unexpected error occurred during reaping: {str(e)}"

if __name__ == "__main__":
    mcp.run()
