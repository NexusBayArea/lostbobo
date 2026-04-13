import os
from app.core.boot.context import boot_context


def load_env():
    """
    Pull raw SB_* env into boot context.
    """

    boot_context.env = {
        k: v for k, v in os.environ.items() if k.startswith("SB_")
    }
