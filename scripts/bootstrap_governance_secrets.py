"""
One-time script to create all governance secrets in Infisical
Run this once during setup.
"""

import os
import sys
from infisical import InfisicalClient


def main():
    token = os.getenv("INFISICAL_TOKEN")
    if not token:
        print("❌ INFISICAL_TOKEN not found in environment.")
        sys.exit(1)

    client = InfisicalClient(
        token=token,
        site_url=os.getenv("INFISICAL_URL", "https://app.infisical.com"),
        environment=os.getenv("INFISICAL_ENV", "prod"),
    )

    defaults = {
        "GOV_USER_REQUEST_RPM": "20",
        "GOV_USER_REQUEST_RPH": "200",
        "GOV_TOKEN_BUDGET_HOURLY": "500000",
        "GOV_MAX_CONTEXT_TOKENS": "12000",
        "GOV_MAX_COMPLETION_TOKENS": "4000",
        "GOV_MAX_STREAM_SECONDS": "60",
        "GOV_MAX_STREAM_IDLE_SECONDS": "30",
        "GOV_MAX_CONCURRENT_SIMULATIONS": "2",
        "GOV_MAX_QUEUE_DEPTH": "20",
        "GOV_MAX_AGENT_HOPS": "5",
        "GOV_MAX_RECURSION_DEPTH": "3",
    }

    project_id = os.getenv("INFISICAL_PROJECT_ID")  # Required
    if not project_id:
        print("❌ Set INFISICAL_PROJECT_ID environment variable")
        sys.exit(1)

    print("🚀 Creating/Updating governance secrets in Infisical...")

    for key, value in defaults.items():
        try:
            # Create or update secret
            client.create_secret(
                secret_name=key,
                secret_value=value,
                project_id=project_id,
                environment=os.getenv("INFISICAL_ENV", "prod"),
            )
            print(f"✅ Created/Updated: {key}")
        except Exception:
            # If already exists, try update
            try:
                client.update_secret(
                    secret_name=key,
                    secret_value=value,
                    project_id=project_id,
                    environment=os.getenv("INFISICAL_ENV", "prod"),
                )
                print(f"✅ Updated: {key}")
            except Exception as update_err:
                print(f"⚠️  Failed {key}: {update_err}")

    print("\n🎉 Governance secrets bootstrap complete!")
    print("You can now adjust values in the Infisical dashboard.")


if __name__ == "__main__":
    main()
