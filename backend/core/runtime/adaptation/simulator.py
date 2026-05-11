# backend/core/runtime/adaptation/simulator.py
from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class SimulationFrame:
    timestamp: float
    regime: str
    entropy: float
    entities: dict[str, float]
    event_count: int
    anomaly_count: int
    reward: float


class TrainingDatasetSimulator:
    """Generates large, realistic training datasets for RL + ML models."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    async def generate_dataset(
        self,
        num_frames: int = 5000,
        regimes: list[str] | None = None,
    ) -> list[SimulationFrame]:
        """Generate full training trajectory."""
        if regimes is None:
            regimes = ["normal", "panic", "disruption"]

        dataset: list[SimulationFrame] = []
        current_regime = "normal"
        causal_id = 0

        for i in range(num_frames):
            t = time.time() - (num_frames - i) * 60

            if self.rng.random() < 0.03:
                current_regime = self.rng.choice(regimes)

            entity_count = 8 + self.rng.randint(0, 12)
            entities = {f"question:{j}": self.rng.uniform(0.1, 0.9) for j in range(entity_count)}

            event_count = 0
            if self.rng.random() < 0.7:
                event_count = self.rng.randint(1, 5)

            anomaly_count = 0
            if self.rng.random() < 0.15:
                anomaly_count = self.rng.randint(1, 3)

            reward = 0.0
            if current_regime == "normal":
                reward = 0.3
            elif current_regime == "disruption":
                reward = -0.2
            elif current_regime == "panic":
                reward = -0.6

            if anomaly_count > 0:
                reward -= anomaly_count * (0.5 + self.rng.random() * 0.5)

            frame = SimulationFrame(
                timestamp=t,
                regime=current_regime,
                entropy=self.rng.uniform(0.1, 2.5),
                entities=entities,
                event_count=event_count,
                anomaly_count=anomaly_count,
                reward=reward,
            )
            dataset.append(frame)
            causal_id += 1

        log.info("Generated %d simulation frames for RL training", len(dataset))
        return dataset

    async def save_dataset(self, dataset: list[SimulationFrame], path: str | None = None):
        """Save dataset to JSON for offline training."""
        if path is None:
            path = "/tmp/simhpc_rl_training_dataset.json"

        serialized = [
            {
                "timestamp": f.timestamp,
                "regime": f.regime,
                "entropy": f.entropy,
                "entity_count": len(f.entities),
                "event_count": f.event_count,
                "anomaly_count": f.anomaly_count,
                "reward": f.reward,
            }
            for f in dataset
        ]

        with open(path, "w") as f:
            json.dump(serialized, f, indent=2)

        log.info("Dataset saved to %s (%d frames)", path, len(dataset))


simulator = TrainingDatasetSimulator()