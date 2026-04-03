"""
SimHPC Panic Button — MCP Skill Script

EMERGENCY: Terminates all RunPod instances and logs the event.
Requires: RUNPOD_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
Injected via Infisical or environment.
"""

import os
import httpx
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def trigger_global_shutdown() -> str:
    """
    EMERGENCY ONLY: Terminates all RunPod instances.
    Logs a critical alert to platform_alerts for post-mortem.
    """
    report: list[str] = []

    # 1. Terminate RunPod Fleet
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    pod_query = {"query": "{ myself { pods { id status } } }"}
    pods_res = httpx.post(
        "https://api.runpod.io/graphql", json=pod_query, headers=headers
    )
    pods = pods_res.json().get("data", {}).get("myself", {}).get("pods", [])

    terminated_count = 0
    for pod in pods:
        term_query = {
            "query": f'mutation {{ terminatePod(input: {{ podId: "{pod["id"]}" }}) {{ id }} }}'
        }
        term_res = httpx.post(
            "https://api.runpod.io/graphql", json=term_query, headers=headers
        )
        if term_res.json().get("errors"):
            report.append(f"⚠️ Failed to terminate {pod['id']}")
        else:
            report.append(f"🛑 Terminated Pod: {pod['id']}")
            terminated_count += 1

    # 2. Log to Admin Dashboard
    supabase.table("platform_alerts").insert({
        "type": "system",
        "severity": "critical",
        "message": f"🚨 GLOBAL PANIC TRIGGERED: {terminated_count} compute resources terminated by Admin.",
        "metadata": {"terminated_count": terminated_count, "total_pods": len(pods)},
    }).execute()

    return "🛑 GLOBAL SHUTDOWN COMPLETE.\n" + "\n".join(report)


if __name__ == "__main__":
    result = trigger_global_shutdown()
    print(result)
