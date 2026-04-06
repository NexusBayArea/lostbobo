"""
Vercel API Entry Point
Fetches secrets from Infisical at runtime - only INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET stored in Vercel
"""

import os
import subprocess

# Only these 2 secrets should be set in Vercel (not exposed to frontend)
INFISICAL_CLIENT_ID = os.environ.get("INFISICAL_CLIENT_ID", "")
INFISICAL_CLIENT_SECRET = os.environ.get("INFISICAL_CLIENT_SECRET", "")
INFISICAL_PROJECT_ID = "ldzztrnghaaonparyggz"


def get_infisical_secret(secret_name: str) -> str:
    """Fetch a single secret from Infisical using machine identity."""
    if not INFISICAL_CLIENT_ID or not INFISICAL_CLIENT_SECRET:
        return ""

    try:
        # Set env vars for infisical CLI
        env = os.environ.copy()
        env["INFISICAL_CLIENT_ID"] = INFISICAL_CLIENT_ID
        env["INFISICAL_CLIENT_SECRET"] = INFISICAL_CLIENT_SECRET

        result = subprocess.run(
            [
                "infisical",
                "secrets",
                "get",
                secret_name,
                "--projectId",
                INFISICAL_PROJECT_ID,
                "--plain",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        if result.returncode == 0:
            value = result.stdout.strip()
            if value and "not found" not in value.lower():
                return value
    except Exception:
        pass
    return ""


def load_secrets_from_infisical():
    """Load all required secrets from Infisical at startup."""
    # Map Infisical secret names to environment variable names
    secret_mapping = {
        "REDIS_URL": "REDIS_URL",
        "SB_URL": "SUPABASE_URL",
        "SB_SECRET_KEY": "SUPABASE_SERVICE_ROLE_KEY",
        "SB_JWT_SECRET": "SUPABASE_JWT_SECRET",
        "SB_PUB_KEY": "SUPABASE_ANON_KEY",
        "MERCURY_API_KEY": "MERCURY_API_KEY",
    }

    for infisical_name, env_name in secret_mapping.items():
        value = get_infisical_secret(infisical_name)
        if value:
            os.environ[env_name] = value


# Load secrets at module import time
load_secrets_from_infisical()

# Import the FastAPI app after secrets are loaded
from api import app
