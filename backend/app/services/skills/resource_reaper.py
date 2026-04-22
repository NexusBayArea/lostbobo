import os
from datetime import datetime, timedelta

import httpx
from mcp.server.fastmcp import FastMCP

from app.core.supabase import supabase

# Initialize FastMCP for your AI agent
mcp = FastMCP("SimHPC-Resource-Reaper")

# Configuration from environment
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")


@mcp.tool()
async def reap_idle_workers() -> str:
    """
    Scans for 'Zombie' RunPod instances that haven't pinged Supabase in 15+ minutes.
    This prevents ghost costs on A40 instances.
    """
    if not RUNPOD_API_KEY:
        return "❌ Error: RUNPOD_API_KEY not found in environment."

    reaped_count = 0
    logs = []

    try:
        # 1. Fetch active pods from RunPod via GraphQL
        async with httpx.AsyncClient() as client:
            query = {"query": "{ myself { pods { id name status } } }"}
            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            response = await client.post("https://api.runpod.io/graphql", json=query, headers=headers)

            if response.status_code != 200:
                return f"❌ RunPod API Error: {response.text}"

            pods = response.json().get("data", {}).get("myself", {}).get("pods", [])

            for pod in pods:
                pod_id = pod["id"]

                # 2. Check the worker_heartbeat table
                res = (
                    supabase.table("worker_heartbeat").select("last_ping").eq("pod_id", pod_id).maybe_single().execute()
                )

                if not res.data:
                    logs.append(f"⚠️ Pod {pod_id} ({pod['name']}) has no heartbeat record.")
                    continue

                # Parse the last ping
                last_ping_str = res.data["last_ping"].replace("Z", "+00:00")
                last_ping = datetime.fromisoformat(last_ping_str)

                # Check if stale (15 minute threshold)
                is_stale = datetime.now(last_ping.tzinfo) - last_ping > timedelta(minutes=15)

                # 3. Terminate if stale and currently 'RUNNING'
                if is_stale and pod["status"] == "RUNNING":
                    terminate_query = {"query": f'mutation {{ terminatePod(input: {{ podId: "{pod_id}" }}) }}'}
                    term_resp = await client.post(
                        "https://api.runpod.io/graphql", json=terminate_query, headers=headers
                    )

                    if term_resp.status_code == 200:
                        reaped_count += 1
                        logs.append(f"💀 Reaped stale Pod {pod_id} (Last seen: {last_ping.strftime('%H:%M:%S')})")
                    else:
                        logs.append(f"❌ Failed to reap Pod {pod_id}: {term_resp.text}")

        if reaped_count == 0:
            return "✅ Fleet Check Complete: All active workers are healthy and heartbeating."

        return f"🛠️ Cleanup Complete. Reaped {reaped_count} workers:\n" + "\n".join(logs)

    except Exception as e:
        return f"❌ Reaper Failure: {str(e)}"


if __name__ == "__main__":
    mcp.run()
