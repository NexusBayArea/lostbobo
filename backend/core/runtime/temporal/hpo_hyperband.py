from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from backend.core.ml.registry import ModelRegistry
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class HyperbandOptimizer:
    """Hyperband: Multi-fidelity bandit-based HPO (very efficient)."""

    def __init__(self):
        self.model_registry = ModelRegistry()

    async def optimize(
        self,
        objective_fn: Callable[[dict[str, Any]], Any],
        param_space: dict[str, tuple[float, float]],
        max_resource: int = 100,  # max training budget (epochs, samples, etc.)
        eta: int = 3,  # downsampling rate
        n_trials: int = 50,
    ) -> dict[str, Any]:
        """Run Hyperband optimization."""
        with trace_context("hpo.hyperband"):
            obs = observability()
            obs.increment("hyperband_runs_total")

            start_time = time.time()

            # Hyperband parameters
            logeta = math.log(eta)
            s_max = int(math.log(max_resource) / logeta)
            b_val = (s_max + 1) * max_resource

            best_loss = float("inf")
            best_params = None
            all_results = []

            for s in range(s_max, -1, -1):
                n_configs = int(math.ceil(b_val / max_resource * (eta**s) / (s + 1)))
                r_val = max_resource * (eta**-s)

                # Initial configurations
                configs = [self._sample_config(param_space) for _ in range(n_configs)]

                for i in range(s + 1):
                    n_i = int(n_configs * (eta**-i))
                    r_i = int(r_val * (eta**i))

                    # Evaluate current batch
                    losses = []
                    for config in configs[:n_i]:
                        loss = await objective_fn({**config, "budget": r_i})
                        losses.append(loss)
                        all_results.append((config, loss, r_i))

                        if loss < best_loss:
                            best_loss = loss
                            best_params = config

                    # Keep top 1/eta configurations
                    if i < s:
                        sorted_indices = np.argsort(losses)
                        configs = [configs[idx] for idx in sorted_indices[: n_i // eta]]

            total_time = time.time() - start_time

            result = {
                "algorithm": "Hyperband",
                "best_params": best_params,
                "best_loss": best_loss,
                "time_seconds": total_time,
                "total_evaluations": len(all_results),
                "efficiency": "high",  # multi-fidelity advantage
            }

            # Save best configuration
            await self.model_registry.register_version(
                model_type="lstm_regime_forecaster",
                metadata={
                    "hpo_method": "hyperband",
                    "best_params": best_params,
                    "best_loss": best_loss,
                },
            )

            obs.gauge("hyperband_best_loss", best_loss)
            return result

    def _sample_config(self, param_space: dict[str, tuple[float, float]]) -> dict[str, Any]:
        """Random sample from search space."""
        config = {}
        for param, (low, high) in param_space.items():
            if isinstance(low, int):
                config[param] = np.random.randint(low, high + 1)
            else:
                config[param] = np.random.uniform(low, high)
        return config
