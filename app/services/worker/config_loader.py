import hashlib
import json
import os

from supabase import Client, create_client

SUPABASE_URL = os.getenv("SB_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SB_SERVICE_ROLE_KEY") or os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def hash_config(config: dict) -> str:
    sorted_json = json.dumps(config, sort_keys=True)
    return hashlib.sha256(sorted_json.encode()).hexdigest()


def load_config(env: str = "prod") -> dict:
    result = (
        supabase.table("config_versions")
        .select("config, hash")
        .eq("env", env)
        .order("created_at", ascending=False)
        .limit(1)
        .single()
        .execute()
    )

    if not result.data:
        raise ValueError(f"No config found for env: {env}")

    return result.data


def check_config_drift(env: str = "prod") -> bool:
    current_config = load_config(env)
    stored_hash = current_config.get("hash")

    config_data = current_config.get("config", {})
    computed_hash = hash_config(config_data)

    return stored_hash != computed_hash


if __name__ == "__main__":
    try:
        config = load_config()
        print(f"Config loaded. Hash: {config.get('hash')}")
    except Exception as e:
        print(f"Error: {e}")
