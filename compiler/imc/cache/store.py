import json
import redis

# Adjust URL as needed for production
r = redis.from_url("redis://localhost:6379/0")


def cache_get(node_id):
    data = r.get(f"imc:{node_id}")
    return json.loads(data) if data else None


def cache_set(node_id, node):
    r.set(f"imc:{node_id}", json.dumps(node))
