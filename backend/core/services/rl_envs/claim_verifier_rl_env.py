import gymnasium as gym
import numpy as np

from backend.kernel.kernel import Kernel


class ClaimVerifierRLEnv(gym.Env):
    """ClaimVerifier as RL environment."""

    def __init__(self, kernel: Kernel):
        super().__init__()
        self.kernel = kernel
        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(96,), dtype=np.float32)

    def step(self, action):
        result = self.kernel.command_bus.route_sync({"type": "CLAIM_VERIFY", "payload": {"strategy": int(action)}})
        reward = result.get("trust_score", 0.0) * 0.8 + (1.0 if result.get("verified") else 0.0) * 0.2
        obs = self.kernel.services["cognition"].get_fused_vector(result)
        return obs, reward, False, False, {}

    def reset(self, *, seed=None, options=None):
        return np.zeros(96, dtype=np.float32), {}


class TrustRuntimeRLEnv(gym.Env):
    """TrustRuntime as RL environment."""

    def __init__(self, kernel: Kernel):
        super().__init__()
        self.kernel = kernel
        self.action_space = gym.spaces.Discrete(3)
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(96,), dtype=np.float32)

    def step(self, action):
        result = self.kernel.command_bus.route_sync(
            {"type": "TRUST_VERIFY", "payload": {"threshold_mode": int(action)}}
        )
        reward = result.get("trust_score", 0.0)
        obs = self.kernel.services["cognition"].get_fused_vector(result)
        return obs, reward, False, False, {}

    def reset(self, *, seed=None, options=None):
        return np.zeros(96, dtype=np.float32), {}
