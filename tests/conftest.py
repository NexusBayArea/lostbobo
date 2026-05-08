import os
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.runtime.chaos_monkey import chaos_monkey, ChaosConfig
from backend.runtime.swarm.swarm_coordinator import SwarmCoordinator
from backend.core.world_model.service import WorldModelService
from backend.core.simulation.runner import SimulationRunner
from backend.runtime.orchestrator.speculative_orchestrator import SpeculativeOrchestrator
from backend.runtime.fallback import FallbackResult


@pytest.fixture(scope="function")
def enable_chaos():
    """Force chaos on for a single test."""
    original = chaos_monkey.config.enabled
    chaos_monkey.config.enabled = True
    chaos_monkey.config.probability = 1.0
    yield
    chaos_monkey.config.enabled = original


@pytest.fixture(scope="function")
def disable_genai():
    """Simulate full GenAI outage."""
    original = os.getenv("GENAI_ENABLED")
    os.environ["GENAI_ENABLED"] = "false"
    yield
    if original is None:
        os.environ.pop("GENAI_ENABLED", None)
    else:
        os.environ["GENAI_ENABLED"] = original


@pytest.fixture
async def full_gameday_fixture():
    """Full end-to-end GameDay simulation fixture."""
    # Mock heavy external dependencies
    with patch("backend.runtime.fallback.GenAIFallback.call_llm_with_fallback") as mock_fallback, \
         patch("backend.core.world_model.service.WorldModelService._persist_to_supabase") as mock_world_update, \
         patch("backend.core.simulation.runner.SimulationRunner.run_monte_carlo_simulation") as mock_physics:

        mock_fallback.return_value = FallbackResult(
            success=True,
            data={"forecast": "Degraded but valid", "content": "Degraded but valid"},
            fallback_used=["rag_deterministic"],
            confidence=0.68,
            degraded=True
        )
        mock_world_update.return_value = True
        mock_physics.return_value = {"result": "degraded_mc", "validation_passed": True, "degraded": True, "fallback_used": ["deterministic"]}

        coordinator = SwarmCoordinator()
        orchestrator = SpeculativeOrchestrator()
        world_model = WorldModelService()
        physics_runner = SimulationRunner()

        yield {
            "coordinator": coordinator,
            "orchestrator": orchestrator,
            "world_model": world_model,
            "physics_runner": physics_runner,
            "chaos_monkey": chaos_monkey,
        }


@pytest.fixture
def mock_supabase():
    """Mock Supabase for governance, auth, and persistence tests."""
    with patch("backend.app.core.supabase.get_supabase_client") as mock_client:
        mock_client.return_value = MagicMock()
        yield mock_client
