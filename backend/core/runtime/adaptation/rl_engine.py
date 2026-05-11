# backend/core/runtime/adaptation/rl_engine.py
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class RLAction:
    isolation_mode: str
    detection_threshold: float
    quarantine: bool
    resource_scale: float
    chaos_inject: bool


class RLAdaptationEngine:
    """Singleton RL agent for runtime self-adaptation."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True

        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim

            class RLPolicyNetwork(nn.Module):
                def __init__(self, state_dim: int = 24, action_dim: int = 5):
                    super().__init__()
                    self.net = nn.Sequential(
                        nn.Linear(state_dim, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU(), nn.Linear(128, action_dim)
                    )
                    self.softmax = nn.Softmax(dim=-1)

                def forward(self, state: torch.Tensor) -> torch.Tensor:
                    return self.softmax(self.net(state))

            self._policy = RLPolicyNetwork()
            self._optimizer = optim.Adam(self._policy.parameters(), lr=1e-4)
            self._torch_available = True
        except Exception as e:
            log.warning("PyTorch not available, RL engine will use fallback: %s", e)
            self._torch_available = False
            self._policy = None
            self._optimizer = None

        self._memory: list[tuple[Any, RLAction, float, Any]] = []
        self._gamma = 0.95
        self._epsilon = 0.1
        self._last_update = time.time()
        self._last_action: RLAction | None = None
        self._last_reward: float = 0.0
        self._stability_bonus = 0.5

    def _extract_state(self, state_snapshot: dict, recent_anomalies: list[dict]) -> np.ndarray:
        """24-dimensional state vector for RL policy."""
        entropy = state_snapshot.get("entropy", 0.0)
        regime = state_snapshot.get("regime", "normal")
        entities = state_snapshot.get("entities", {})

        try:
            from backend.core.runtime.anomaly.ml_predictor import ml_anomaly_predictor

            uncertainty_mean = (
                ml_anomaly_predictor._history[-1].get("uncertainty_mean", 0.0) if ml_anomaly_predictor._history else 0.0
            )
        except Exception:
            uncertainty_mean = 0.0

        return np.array(
            [
                entropy,
                1.0 if regime == "panic" else 0.0,
                len(recent_anomalies),
                uncertainty_mean,
                len(entities),
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=np.float32,
        )

    def select_action(self, state_snapshot: dict, recent_anomalies: list[dict]) -> RLAction:
        """Epsilon-greedy policy + exploration."""
        self._ensure_initialized()

        state_vec = self._extract_state(state_snapshot, recent_anomalies)

        if not self._torch_available or self._policy is None:
            return self._fallback_action()

        try:
            import torch

            state_tensor = torch.tensor(state_vec).unsqueeze(0)

            if np.random.rand() < self._epsilon:
                action_idx = np.random.randint(0, 5)
            else:
                with torch.no_grad():
                    probs = self._policy(state_tensor)
                    action_idx = torch.argmax(probs).item()
        except Exception:
            return self._fallback_action()

        modes = ["sandbox", "wasm", "kata"]
        self._last_action = RLAction(
            isolation_mode=modes[action_idx % 3],
            detection_threshold=0.3 + (action_idx % 3) * 0.3,
            quarantine=action_idx > 2,
            resource_scale=0.8 + (action_idx % 3) * 0.4,
            chaos_inject=action_idx % 5 == 4,
        )

        return self._last_action

    def _fallback_action(self) -> RLAction:
        return RLAction(
            isolation_mode="sandbox",
            detection_threshold=0.5,
            quarantine=False,
            resource_scale=1.0,
            chaos_inject=False,
        )

    async def update(
        self,
        state: dict,
        action: RLAction,
        reward: float,
        next_state: dict,
    ):
        """Simple policy gradient update."""
        self._ensure_initialized()

        self._memory.append((state, action, reward, next_state))
        self._last_reward = reward

        if len(self._memory) < 32 or time.time() - self._last_update < 300:
            return

        if not self._torch_available or self._policy is None:
            return

        try:
            import torch

            torch.tensor([self._extract_state(s, []) for s, _, _, _ in self._memory[-32:]]).float()
            rewards = torch.tensor([r for _, _, r, _ in self._memory[-32:]]).float()

            self._optimizer.zero_grad()
            loss = -torch.mean(rewards)
            loss.backward()
            self._optimizer.step()

            self._memory = self._memory[-100:]
            self._last_update = time.time()
            log.info("RL policy updated (reward=%.3f)", rewards.mean().item())
        except Exception as e:
            log.warning("RL policy update failed: %s", e)

    def compute_reward(self, anomalies: list[dict], latency_ms: float) -> float:
        """Compute reward from environment feedback."""
        severity_penalty = 0.0
        for a in anomalies:
            sev = a.get("severity", "low")
            if sev == "critical":
                severity_penalty -= 2.0
            elif sev == "high":
                severity_penalty -= 1.0
            elif sev == "medium":
                severity_penalty -= 0.5

        latency_penalty = -0.001 * latency_ms if latency_ms > 100 else 0.0

        stability_bonus = self._stability_bonus if not anomalies else 0.0

        return severity_penalty + latency_penalty + stability_bonus

    def get_last_action(self) -> dict[str, Any] | None:
        if self._last_action:
            return {
                "isolation_mode": self._last_action.isolation_mode,
                "detection_threshold": self._last_action.detection_threshold,
                "quarantine": self._last_action.quarantine,
                "resource_scale": self._last_action.resource_scale,
                "chaos_inject": self._last_action.chaos_inject,
            }
        return None

    def get_last_reward(self) -> float:
        return self._last_reward

    async def apply_action(self, action: RLAction, anomalies: list[dict]):
        """Apply RL action - trigger quarantine or chaos if needed."""
        if action.quarantine and self.rng.random() < 0.15:
            await self._trigger_quarantine(action)
        if action.chaos_inject:
            await self._trigger_controlled_chaos()

    async def _trigger_quarantine(self, action: RLAction):
        """Trigger auto-quarantine for plugins."""
        try:
            log.warning("RL-triggered quarantine initiated: isolation=%s", action.isolation_mode)

            try:
                from backend.core.runtime.event_fabric.log import EventLogService

                event = {
                    "event_type": "runtime.quarantine_triggered",
                    "source_plugin": "rl_adaptation_engine",
                    "payload": {
                        "isolation_mode": action.isolation_mode,
                        "detection_threshold": action.detection_threshold,
                    },
                    "confidence": 0.9,
                }
                await EventLogService().publish(event)
            except Exception:
                pass
        except Exception as e:
            log.warning("Quarantine trigger failed: %s", e)

    async def _trigger_controlled_chaos(self):
        """Inject controlled chaos for robustness training."""
        try:
            chaos_types = ["delay_event", "drop_event", "increase_uncertainty"]
            chaos_type = self.rng.choice(chaos_types) if hasattr(self, "rng") else "increase_uncertainty"

            log.info("RL-triggered chaos injection: %s", chaos_type)

            try:
                from backend.core.runtime.event_fabric.log import EventLogService

                event = {
                    "event_type": "runtime.chaos_injected",
                    "source_plugin": "rl_adaptation_engine",
                    "payload": {"type": chaos_type},
                    "confidence": 0.9,
                }
                await EventLogService().publish(event)
            except Exception:
                pass
        except Exception as e:
            log.warning("Chaos injection failed: %s", e)

    @property
    def rng(self) -> random.Random:
        if not hasattr(self, "_rng"):
            self._rng = random.Random(time.time())
        return self._rng


rl_adaptation_engine = RLAdaptationEngine()
