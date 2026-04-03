#!/usr/bin/env python3
"""
SimHPC Alpha Debugger
Run inside worker container to verify Redis + Supabase connectivity.

Usage:
  docker exec -it <container> python3 debug.py
  # or on RunPod:
  python3 debug.py
"""

import os
from redis import Redis
from supabase import create_client

redis_url = os.getenv("REDIS_URL")
sb_url = os.getenv("SUPABASE_URL")
sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("--- SimHPC Alpha Debugger ---")

# 1. Redis
try:
    if not redis_url:
        raise ValueError("Missing REDIS_URL env var")
    r = Redis.from_url(redis_url, socket_connect_timeout=5)
    r.ping()
    print(f"REDIS: Connected ({redis_url})")
except Exception as e:
    print(f"REDIS: Failed - {e}")

# 2. Supabase
try:
    if not sb_url or not sb_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sb = create_client(sb_url, sb_key)
    sb.table("worker_heartbeat").select("*").limit(1).execute()
    print(f"SUPABASE: Connected & worker_heartbeat table accessible")
except Exception as e:
    print(f"SUPABASE: Failed - {e}")
