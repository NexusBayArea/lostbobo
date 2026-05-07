import pytest
from unittest.mock import patch

from backend.core.world_model.service import WorldModelService
from backend.core.world_model.schema import WorldState, Uncertainty


@pytest.fixture
def world_model():
    return WorldModelService()


@pytest.mark.asyncio
async def test_world_model_update_with_fallback(world_model):
    """World Model handles update during GenAI/Supabase chaos."""
    with patch(
        "backend.core.world_model.service.WorldModelService._persist_to_supabase",
        side_effect=[Exception("Supabase timeout"), True],
    ):
        state = WorldState(
            entities={"battery": {"energy": 42.0}},
            uncertainty=Uncertainty(mean=0.05, std=0.02),
        )

        result = await world_model.update(state, domain="energy")

    assert result.success is True
    assert "fallback" in result.fallback_used
    assert result.state_id is not None


@pytest.mark.asyncio
async def test_uncertainty_propagation_under_chaos(world_model):
    with patch(
        "backend.core.world_model.service.WorldModelService.propagate_uncertainty"
    ) as mock_prop:
        mock_prop.return_value = {"entities": {"battery": {"energy": 41.8}}}

        result = await world_model.propagate_uncertainty("energy", scenarios=5)

    assert "monte_carlo" in result  # even under chaos
