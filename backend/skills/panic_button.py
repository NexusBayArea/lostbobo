import os

import redis
import runpod

from app.core.supabase_client import supabase  # Standardized SB client

# 1. Initialize Cloud Controls
runpod.api_key = os.getenv("RP_API_KEY")
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))


def total_fleet_kill():
    """
    EMERGENCY PROTOCOL:
    1. Purges all job queues.
    2. Terminates every active RunPod worker.
    3. Logs the panic event to Supabase for audit.
    """
    print("🚨 PANIC BUTTON ACTIVATED: Initiating Total Fleet Kill...")

    try:
        # A. Purge Redis Queues (Immediate stop of new job pickup)
        redis_client.delete("simhpc_jobs")
        redis_client.delete("simhpc_priority_jobs")
        print("✔ Redis queues cleared.")

        # B. Identify and Terminate RunPod Workers
        all_pods = runpod.get_pods()
        # Only target pods matching your v3.5.0 naming convention
        target_pods = [p for p in all_pods if "simhpc-worker" in p.get("name", "")]

        if not target_pods:
            print("ℹ No active pods found in the cloud.")
        else:
            for pod in target_pods:
                runpod.terminate_pod(pod["id"])
                print(f"\u2714 Terminated Pod: {pod['id']} ({pod['name']})")

        # C. Log Event to Persistent Backbone
        supabase.table("platform_alerts").insert(
            {
                "event_type": "PANIC_TERMINATION",
                "severity": "CRITICAL",
                "message": f"Manual fleet kill triggered. Terminated {len(target_pods)} pods.",
                "metadata": {"pod_ids": [p["id"] for p in target_pods]},
            }
        ).execute()

        print("🚨 TOTAL FLEET KILL COMPLETE. Cloud burn is now $0.")
        return True

    except Exception as e:
        print(f"❌ PANIC BUTTON FAILURE: {str(e)}")
        return False


if __name__ == "__main__":
    total_fleet_kill()
