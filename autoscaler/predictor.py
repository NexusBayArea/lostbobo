"""
Optional forecasting for autoscaler
"""

import numpy as np


class SimplePredictor:
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.history = []

    def add_observation(self, queue_depth: int):
        """Add a queue depth observation to history"""
        self.history.append(queue_depth)
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def predict_next(self) -> int:
        """Predict next queue depth using simple moving average"""
        if len(self.history) < 2:
            return self.history[-1] if self.history else 0

        # Simple moving average
        return int(np.mean(self.history))

    def get_trend(self) -> str:
        """Get trend direction"""
        if len(self.history) < 2:
            return "stable"

        recent_avg = (
            np.mean(self.history[-3:])
            if len(self.history) >= 3
            else np.mean(self.history)
        )
        older_avg = (
            np.mean(self.history[:-3])
            if len(self.history) >= 6
            else np.mean(self.history[: len(self.history) // 2])
        )

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"


def get_predictor() -> SimplePredictor:
    """Get predictor instance"""
    return SimplePredictor()
