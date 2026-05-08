from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog

from backend.app.kernel.command_bus import command_bus
from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class RLStep:
    state_hash: str
    action: str
    reward: float
    next_state_hash: str | None
    done: bool
    metadata: dict[str, Any]


class ReinforcementLearningService:
    """Kernel-centered RL for agent policy learning and simulation optimization."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        # Q-table: state_hash → action → Q-value
        self.policy: dict[str, dict[str, float]] = {}

    async def step(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Single RL step."""
        job_id = payload["job_id"]
        current_state = payload["state"]

        state_hash = await self.kernel.services["state_hasher"].hash(current_state)

        # Select action
        action = self._select_action(state_hash, payload.get("available_actions", []))

        # Execute action via Kernel
        action_result = await command_bus.route({"type": f"ACTION_{action.upper()}", "payload": payload})

        # Compute reward
        reward = await self._compute_reward(payload, action_result, action)

        next_state_hash = await self.kernel.services["state_hasher"].hash(action_result)

        # Store trajectory
        step_data = RLStep(
            state_hash=state_hash,
            action=action,
            reward=reward,
            next_state_hash=next_state_hash,
            done=payload.get("done", False),
            metadata=action_result,
        )
        await self.supabase.record_event("rl_step", {"job_id": job_id, "step": step_data.__dict__})

        # Update policy
        await self._update_policy(state_hash, action, reward, next_state_hash)

        return {
            "action": action,
            "reward": reward,
            "next_state": action_result,
            "q_value": self.policy.get(state_hash, {}).get(action, 0.0),
        }

    def _select_action(self, state_hash: str, available_actions: list[str]) -> str:
        if not available_actions:
            return "default"
        if np.random.rand() < 0.1:
            return np.random.choice(available_actions)
        q_values = self.policy.get(state_hash, {})
        if not q_values:
            return np.random.choice(available_actions)
        return max(q_values, key=q_values.get)

    async def _compute_reward(self, payload: dict[str, Any], result: dict[str, Any], action: str) -> float:
        reward = 0.0
        trust_score = result.get("trust_score", 0.0)
        reward += trust_score * 0.4
        reward += result.get("novelty_score", 0.5) * 0.25
        if "physics" in payload.get("domain", ""):
            reward += result.get("validation_passed", False) * 0.2
        if result.get("safety_passed", True):
            reward += 0.15
        if result.get("loop_detected", False):
            reward -= 1.0
        return float(np.clip(reward, -1.0, 1.0))

    async def _update_policy(self, state_hash: str, action: str, reward: float, next_state_hash: str):
        if state_hash not in self.policy:
            self.policy[state_hash] = {}
        if action not in self.policy[state_hash]:
            self.policy[state_hash][action] = 0.0
        current_q = self.policy[state_hash][action]
        next_max_q = max(self.policy.get(next_state_hash, {}).values(), default=0.0)
        self.policy[state_hash][action] = current_q + 0.1 * (reward + 0.95 * next_max_q - current_q)
        if len(self.policy) % 50 == 0:
            await self.supabase.save_rl_policy_snapshot(self.policy)
