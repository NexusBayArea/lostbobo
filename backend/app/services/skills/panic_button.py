import os

import httpx
import redis
from mcp.server.fastmcp import FastMCP
from supabase import create_client

# Initialize FastMCP for your AI agent
mcp = FastMCP("SimHPC-Panic-Button")

# Initialize Admin Clients using existing core settings
# Assumes these env vars are provided by the orchestration environment
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))


@mcp.tool()
async def trigger_global_shutdown() -> str:
    """
    EMERGENCY ONLY: Terminates all RunPod instances and clears the simulation queue.
    """
    if not os.getenv("RUNPOD_API_KEY"):
        return "❌ Error: RUNPOD_API_KEY not found."

    report = []

    # 1. Terminate RunPod Fleet
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {os.getenv('RUNPOD_API_KEY')}"}
            # Fetch all pods
            pod_query = {"query": "{ myself { pods { id } } }"}
            pods_res = await client.post(
                "https://api.runpod.io/graphql", json=pod_query, headers=headers
            )
            pods = pods_res.json()["data"]["myself"]["pods"]

            for pod in pods:
                term_query = {
                    "query": f'mutation {{ terminatePod(input: {{ podId: "{pod["id"]}" }}) }}'
                }
                await client.post("https://api.runpod.io/graphql", json=term_query, headers=headers)
                report.append(f"💥 Terminated Pod: {pod['id']}")
    except Exception as e:
        report.append(f"❌ Error during RunPod termination: {str(e)}")

    # 2. Flush Redis Queue
    try:
        redis_client.flushall()
        report.append("🧹 Redis Queue Flushed (All pending jobs deleted).")
    except Exception as e:
        report.append(f"❌ Error during Redis flush: {str(e)}")

    # 3. Log to Admin Dashboard
    try:
        supabase.table("platform_alerts").insert(
            {
                "type": "system",
                "severity": "critical",
                "message": "🚨 GLOBAL PANIC TRIGGERED: All compute resources terminated by Admin.",
                "metadata": {"terminated_count": len(pods) if "pods" in locals() else 0},
            }
        ).execute()
    except Exception as e:
        report.append(f"❌ Error logging to Supabase: {str(e)}")

    return "🛑 GLOBAL SHUTDOWN COMPLETE.\n" + "\n".join(report)


if __name__ == "__main__":
    mcp.run()
