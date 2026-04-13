import os


def normalize():
    """
    Translate SB_* into internal schema.
    """

    mapping = {
        "APP_URL": "SB_URL",
        "DATA_URL": "SB_DATA_URL",
        "JWT_SECRET": "SB_JWT_SECRET",
        "PUBLIC_KEY": "SB_PUB_KEY",
        "SECRET_KEY": "SB_SECRET_KEY",
        "API_TOKEN": "SB_TOKEN",
    }

    for internal, external in mapping.items():
        os.environ[internal] = os.environ.get(external, "")
