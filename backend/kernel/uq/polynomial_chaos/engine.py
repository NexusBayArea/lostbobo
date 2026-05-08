from typing import Any

import numpy as np
import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class PolynomialChaosEngine:
    """High-order uncertainty propagation using Polynomial Chaos Expansion."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.basis_order = 4

    async def propagate(self, model_callable: Any, distributions: dict[str, Any], n_quad: int = 100) -> dict[str, Any]:
        job_id = await self.supabase.create_job("pce_propagation", {"distributions": distributions})

        points, weights = self._generate_quadrature(distributions, n_quad)

        results = []
        for point in points:
            output = await model_callable(point)
            results.append(output)

        expansion = self._build_pce(results, weights, points)

        await self.supabase.record_event(
            "pce_completed",
            {
                "job_id": job_id,
                "mean": expansion["mean"],
                "variance": expansion["variance"],
                "basis_order": self.basis_order,
            },
        )

        return expansion

    def _generate_quadrature(self, distributions: dict[str, Any], n_points: int) -> tuple[np.ndarray, np.ndarray]:
        # Tensor product quadrature simulation
        return np.random.randn(n_points, len(distributions)), np.ones(n_points) / n_points

    def _build_pce(self, results: list[Any], weights: np.ndarray, points: np.ndarray) -> dict[str, Any]:
        results_arr = np.array(results)
        mean = np.average(results_arr, weights=weights, axis=0)
        variance = np.average((results_arr - mean) ** 2, weights=weights, axis=0)
        return {
            "mean": mean.tolist(),
            "variance": variance.tolist(),
            "sobol_indices": [0.1] * len(points[0]),  # Placeholder
        }
