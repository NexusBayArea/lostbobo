import hashlib
import random

import numpy as np


class DeterministicSeedManager:
    def derive_seed(self, execution_id: str) -> int:
        """Produce a deterministic 32-bit integer seed from an execution ID."""
        digest = hashlib.sha256(execution_id.encode()).hexdigest()
        return int(digest[:8], 16)

    def apply_seed(self, seed: int):
        """Apply the seed globally to random, numpy."""
        random.seed(seed)
        np.random.seed(seed)
