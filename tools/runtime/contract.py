import sys
from pathlib import Path


class ExecutionContract:
    """
    Single source of truth for:
    - import root
    - runtime paths
    - DAG resolution
    """

    def __init__(self):
        self.root = Path(__file__).resolve().parents[2]
        self.src = self.root / "src"

    def apply(self):
        """
        Force deterministic import resolution across CI + local.
        """
        sys.path.insert(0, str(self.src))
        sys.path.insert(0, str(self.root))
        return self


CONTRACT = ExecutionContract()
CONTRACT.apply()
