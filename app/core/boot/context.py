from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BootContext:
    env: Dict[str, str]
    settings: Any = None
    initialized: bool = False


boot_context = BootContext(env={})
