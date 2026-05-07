import logging
import os

from infisical import InfisicalClient

log = logging.getLogger(__name__)

_client: InfisicalClient | None = None


def get_infisical_client() -> InfisicalClient:
    global _client
    if _client is None:
        try:
            _client = InfisicalClient(
                token=os.getenv("INFISICAL_TOKEN"),
                site_url=os.getenv("INFISICAL_URL", "https://app.infisical.com"),
                environment=os.getenv("INFISICAL_ENV", "prod"),
            )
            log.info("✅ Infisical client initialized")
        except Exception as e:
            log.error(f"Infisical initialization failed: {e}")
            raise
    return _client


# Optional: JIT inject common secrets into environment (for backward compatibility)
def infisical_jit_inject(keys: list[str] | None = None):
    """Inject secrets from Infisical into os.environ"""
    client = get_infisical_client()
    if keys is None:
        keys = [
            "GOV_USER_REQUEST_RPM",
            "GOV_TOKEN_BUDGET_HOURLY",
            "GOV_MAX_CONCURRENT_SIMULATIONS",
            "OPENAI_API_KEY",
        ]
    for key in keys:
        try:
            secret = client.get_secret(key)
            if secret and secret.secret_value:
                os.environ[key] = secret.secret_value
                log.debug(f"Injected secret: {key}")
        except Exception as e:
            log.warning(f"Could not inject {key}: {e}")
