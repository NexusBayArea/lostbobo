"""Monte Carlo Path Simulation for Drift & Liquidity Detection."""

from __future__ import annotations

import numpy as np


def simulate_paths(
    historical_prices: list[float],
    steps: int = 100,
    iterations: int = 10000,
    dt: float = 1 / 252,
    include_jumps: bool = True,
) -> np.ndarray:
    """Simulate multiple price paths using Geometric Brownian Motion + optional Poisson jumps."""
    if len(historical_prices) < 2:
        last_price = historical_prices[-1] if historical_prices else 100.0
        return np.full((iterations, steps), last_price)

    log_returns = np.diff(np.log(historical_prices))
    mu = np.mean(log_returns) / dt
    sigma = np.std(log_returns) / np.sqrt(dt)

    s0 = historical_prices[-1]
    paths = np.zeros((iterations, steps + 1))
    paths[:, 0] = s0

    z = np.random.normal(0, 1, size=(iterations, steps))

    for t in range(1, steps + 1):
        paths[:, t] = paths[:, t - 1] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z[:, t - 1]
        )

    if include_jumps:
        lambda_jump = 0.1
        jump_size = np.random.normal(0.0, 0.03, size=(iterations, steps))
        jumps = np.random.poisson(lambda_jump * dt, size=(iterations, steps))
        paths[:, 1:] *= np.exp(jumps * jump_size)

    return paths[:, 1:]