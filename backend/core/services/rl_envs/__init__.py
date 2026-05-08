import gymnasium as gym
import numpy as np

from backend.kernel.kernel import Kernel


class PhysicsRLWrapper(gym.Env):
    """Physics Engine as RL environment."""

    def __init__(self, kernel: Kernel):
        super().__init__()
        self.kernel = kernel
        self.action_space = gym.spaces.Discrete(8)
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(64,), dtype=np.float32)

    def step(self, action):
        result = self.kernel.command_bus.route_sync({"type": "PHYSICS_SIMULATE", "payload": {"rl_action": int(action)}})
        reward = result.get("validation_passed", False) * 1.0 + result.get("novelty", 0.0) * 0.5
        obs = self.kernel.services["cognition"].get_fused_vector(result)
        return obs, reward, result.get("done", False), False, {}

    def reset(self, *, seed=None, options=None):
        return np.zeros(64, dtype=np.float32), {}


class RAGRLEnv(gym.Env):
    """RAG Router as RL environment."""

    def __init__(self, kernel: Kernel):
        super().__init__()
        self.kernel = kernel
        self.action_space = gym.spaces.Discrete(5)
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(96,), dtype=np.float32)

    def step(self, action):
        result = self.kernel.command_bus.route_sync({"type": "RAG_QUERY", "payload": {"layer": int(action)}})
        reward = result.get("relevance_score", 0.0) * 0.7 + (1.0 if result.get("cache_hit") else 0.0) * 0.3
        obs = self.kernel.services["cognition"].get_fused_vector(result)
        return obs, reward, False, False, {}

    def reset(self, *, seed=None, options=None):
        return np.zeros(96, dtype=np.float32), {}
