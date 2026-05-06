#!/usr/bin/env python3
"""Test script for Beam Orchestrator + Hypothesis system."""

import asyncio

from backend.core.agents.rag_agent import RAGAgent
from backend.core.agents.reasoning_agent import ReasoningAgent
from backend.core.agents.simulation_agent import SimulationAgent
from backend.core.orchestrator.beam_orchestrator import BeamOrchestrator
from backend.runtime.rag.router import RAGRouter


async def main() -> None:
    agents = [
        ReasoningAgent(),
        RAGAgent(),
        SimulationAgent(),
    ]

    orchestrator = BeamOrchestrator(
        agents=agents,
        sim_runner=None,
        rag=RAGRouter(),
        config={
            "beam_width": 5,
            "exit_threshold": 0.85,
            "stages": ["plausibility", "rag", "simulation"],
        },
    )

    result = await orchestrator.run(
        query="How does 4C fast charging affect lithium plating in NMC811 cells?",
        tenant_id="public",
    )

    print("=== Beam Orchestrator Result ===")
    print(f"ID: {result.id}")
    print(f"Stage: {result.stage}")
    print(f"Trust Score: {result.trust_score:.3f}")
    print(f"Claim: {result.claim}")
    print(f"Simulation Params: {result.sim_params}")


if __name__ == "__main__":
    asyncio.run(main())
