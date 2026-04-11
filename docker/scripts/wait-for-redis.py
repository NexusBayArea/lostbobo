import redis
import os
import time
import sys

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

print(f"⏳ Waiting for Redis at {REDIS_URL}...")

for i in range(60):
    try:
        r = redis.from_url(REDIS_URL)
        if r.ping():
            print("✅ Redis ready")
            sys.exit(0)
    except Exception as e:
        print(f"Redis not ready... {i}/60 - Error: {e}")
        time.sleep(2)

print("❌ Redis failed to respond")
sys.exit(1)
