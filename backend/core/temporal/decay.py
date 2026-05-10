from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass
class DecayingSignal:
    """Signal with native half-life decay and regime acceleration."""

    value: float
    created_at: float
    half_life_seconds: float
    regime_multiplier: float = 1.0

    def current_value(self, current_time: float | None = None) -> float:
        if current_time is None:
            current_time = time.time()
        elapsed = current_time - self.created_at
        if elapsed <= 0:
            return self.value

        effective_half_life = self.half_life_seconds / self.regime_multiplier
        decay_factor = math.exp(-0.693147 * elapsed / effective_half_life)
        return self.value * decay_factor

    def current_uncertainty(self, base_uncertainty: float, current_time: float | None = None) -> float:
        decay = 1.0 - (self.current_value(current_time) / self.value)
        return min(1.0, base_uncertainty + decay * 0.4)
