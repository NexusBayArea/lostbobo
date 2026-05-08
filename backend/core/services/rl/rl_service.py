from typing import Any

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

from backend.app.kernel.command_bus import command_bus
from backend.core.services.rl.rl_service import SimHPCEnv
from backend.core.services.rl_envs import PhysicsRLWrapper, RAGRLEnv
from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel


class ReinforcementLearningService:
    """Kernel-centered PPO supporting multiple components (Swarm, Autonomous, Physics, RAG)."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.model = None

    async def get_or_create_model(self, component: str = "general") -> PPO:
        if self.model is None:
            env = make_vec_env(lambda: self._get_env(component), n_envs=1)
            self.model = PPO(
                "MlpPolicy",
                env,
                verbose=1,
                learning_rate=3e-4,
                n_steps=2048,
                batch_size=64,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                tensorboard_log="./tensorboard/simhpc_ppo",
            )
        return self.model

    def _get_env(self, component: str):
        if component == "physics":
            return PhysicsRLWrapper(self.kernel)
        if component == "rag":
            return RAGRLEnv(self.kernel)
        return SimHPCEnv(self.kernel)

    async def step(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Unified PPO step — called by any component via Kernel command"""
        component = payload.get("component", "general")
        job_id = payload["job_id"]

        model = await self.get_or_create_model(component)
        obs = await self.kernel.services["cognition"].get_fused_vector(payload.get("state", {}))

        action, _ = model.predict(obs, deterministic=False)

        # Execute the chosen action through Kernel
        result = await command_bus.route({"type": f"ACTION_{int(action)}", "payload": payload})

        reward = float(result.get("reward", 0.0))

        # Online learning step
        model.learn(total_timesteps=1, reset_num_timesteps=False)

        # Persist to Supabase
        await self.supabase.record_event(
            "rl_step",
            {
                "job_id": job_id,
                "component": component,
                "action": int(action),
                "reward": reward,
                "trust_score": result.get("trust_score"),
            },
        )

        return {"action": int(action), "reward": reward, "next_state": result}
