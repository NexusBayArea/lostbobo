"""Pod 2: Monte Carlo Drift Detection + Liquidity Validation."""

from __future__ import annotations

import numpy as np

from backend.runtime.simhpc.monte_carlo import simulate_paths


class DriftDetector:
    def __init__(self, sensitivity: float = 2.5):
        self.sensitivity = sensitivity

    def detect_liquidity_distortion(self, market_history: list[float], current_price: float) -> bool:
        """Monte Carlo simulation to detect anomalous price moves."""
        paths = simulate_paths(historical_prices=market_history, steps=100, iterations=10000, include_jumps=True)

        expected_range = np.percentile(paths[:, -1], [1, 99])

        if current_price < expected_range[0] or current_price > expected_range[1]:
            return True

        return False


class LiquidityAggregator:
    def calculate_arb_opportunity(self, price_a: float, price_b: float) -> float:
        """Cross-platform arbitrage opportunity minus fees."""
        fees = 0.02
        return abs(price_a - price_b) - fees
