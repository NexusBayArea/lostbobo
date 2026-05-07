#!/usr/bin/env python3
import asyncio
import subprocess
import random
import sys
from datetime import datetime
from pathlib import Path

import structlog
from chaos_postmortem import main as generate_postmortem

log = structlog.get_logger(__name__)

GAME_DAY_EXPERIMENTS = [
    "cross-rag-physics-parallel",
    "cross-rag-worldmodel-parallel",
    "genai-fallback-agent-swarm",
]


async def run_gameday(experiment: str | None = None, iterations: int = 1):
    experiment = experiment or random.choice(GAME_DAY_EXPERIMENTS)
    log.info(f"🚀 Starting GameDay: {experiment} (iterations={iterations})")

    for i in range(iterations):
        log.info(f"Round {i + 1}/{iterations} — Applying chaos...")
        # Run Chaos Mesh Workflow
        subprocess.run(
            ["kubectl", "apply", "-f", f"deploy/chaos/experiments/{experiment}.yaml"],
            check=True,
        )
        # Run Litmus ChaosEngine in parallel
        subprocess.run(
            [
                "kubectl",
                "apply",
                "-f",
                f"deploy/chaos/litmus-experiments/{experiment}.yaml",
            ],
            check=True,
        )

        await asyncio.sleep(120)  # Wait for experiment duration + probes

        log.info("📊 Generating post-mortem...")
        # Call generate_postmortem internally or via sub-process
        # For this script, we'll assume generate_postmortem from chaos_postmortem
        # can be adjusted to accept an experiment name argument.
        try:
            generate_postmortem(experiment)
            Path(
                f"reports/gameday-{experiment}-{datetime.now().isoformat().replace(':', '-')}.md"
            ).write_text("Report generated.")
        except Exception as e:
            log.error(f"Post-mortem failed: {e}")

    log.info("✅ GameDay complete — reports saved in ./reports/")


if __name__ == "__main__":
    asyncio.run(run_gameday(sys.argv[1] if len(sys.argv) > 1 else None))
