import pytest
from unittest.mock import patch

from backend.core.simulation.runner import SimulationRunner
from backend.physics.coupler import MultiPhysicsCoupler


@pytest.mark.asyncio
async def test_physics_engine_monte_carlo_fallback():
    runner = SimulationRunner()

    with patch(
        "backend.runtime.simhpc.monte_carlo.simulate_paths",
        side_effect=Exception("GPU failure"),
    ):
        with patch(
            "backend.core.physics.coupler.MultiPhysicsCoupler.fallback_deterministic"
        ) as mock_det:
            mock_det.return_value = {
                "result": "degraded simulation",
                "validation_passed": True,
            }

            result = await runner.run_monte_carlo_simulation(
                params={"iterations": 1000}
            )

    assert result["degraded"] is True
    assert result["validation_passed"] is True
    assert "deterministic" in result["fallback_used"]


@pytest.mark.asyncio
async def test_multi_physics_coupler_robustness():
    coupler = MultiPhysicsCoupler()

    with patch.object(
        coupler, "run_coupled_simulation", side_effect=Exception("Coupler crash")
    ):
        result = await coupler.run_with_fallback({"thermal": {}, "electrical": {}})

    assert result["status"] == "degraded"
    assert "robustness_check" in result
