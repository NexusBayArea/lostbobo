import hashlib
import json


from supabase import Client, create_client

from app.core.config import get_settings

settings = get_settings()

if not settings.APP_URL or not settings.API_TOKEN:
    raise ValueError(
        "Normalized Infrastructure secrets (APP_URL/API_TOKEN) are required"
    )

supabase: Client = create_client(settings.APP_URL, settings.API_TOKEN)


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
