import pytest
from unittest.mock import AsyncMock

from backend.runtime.swarm.swarm_coordinator import ForecastingQuestion


@pytest.mark.asyncio
async def test_full_gameday_simulation(
    full_gameday_fixture, enable_chaos, disable_genai
):
    """Complete end-to-end GameDay simulation under maximum chaos + GenAI outage."""
    fixture = full_gameday_fixture

    # 1. Swarm Coordinator
    question = ForecastingQuestion(query="Battery optimization under stress")
    result = await fixture["coordinator"].evaluate(question)
    assert result["decision"] in ["PROCEED", "ABORT_LOW_CONFIDENCE"]

    # 2. Speculative Orchestrator (multiple agents)
    agent_result = await fixture["orchestrator"]._run_agent_resilient(
        agent=AsyncMock(), query="physics query", tenant_id="t1", name="physics_agent"
    )
    assert agent_result.degraded is True

    # 3. World Model persistence under chaos
    state = {"entities": {"battery": {"energy": 42.0}}}
    wm_result = await fixture["world_model"].update(state, domain="energy")
    assert wm_result["success"] is True

    # 4. Physics Engine
    sim_result = await fixture["physics_runner"].run_monte_carlo_simulation(
        {"iterations": 500}
    )
    assert sim_result["validation_passed"] is True

    print("✅ Full GameDay E2E completed under chaos + GenAI outage")
