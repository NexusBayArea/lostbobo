from __future__ import annotations

import math
import time


class TrustDecayEngine:
    """Applies a decay factor to trust scores based on time and anomaly events.
    Called whenever a new trust evaluation event is processed, or on a schedule."""

    DECAY_RATE_PER_HOUR = 0.02  # 2% per hour without positive events
    ANOMALY_PENALTY = 0.05  # per anomaly event

    def decay(self, last_trust_score: float, last_eval_time: float, recent_anomaly_count: int = 0) -> float:
        """Returns new trust score after time decay and anomaly penalty."""
        hours_passed = (time.time() - last_eval_time) / 3600
        score = last_trust_score * math.exp(-self.DECAY_RATE_PER_HOUR * hours_passed)
        score -= recent_anomaly_count * self.ANOMALY_PENALTY
        return max(0.0, min(1.0, score))
