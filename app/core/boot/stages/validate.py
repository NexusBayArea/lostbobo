REQUIRED = [
    "SB_URL",
    "SB_TOKEN",
    "SB_SECRET_KEY",
    "SB_JWT_SECRET",
    "SB_PUB_KEY",
    "SB_DATA_URL",
]


def validate_env(env: dict):
    missing = [k for k in REQUIRED if k not in env or not env[k]]

    if missing:
        raise RuntimeError(
            "BOOT FAILURE: missing env vars:\n"
            + "\n".join(f"- {m}" for m in missing)
        )
