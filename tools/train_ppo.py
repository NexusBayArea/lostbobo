import argparse
import asyncio
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback

from backend.core.services.rl.rl_service import SimHPCEnv
from backend.kernel.kernel import Kernel


def parse_args():
    parser = argparse.ArgumentParser(description="Offline PPO Training for SimHPC")
    parser.add_argument(
        "--episodes", type=int, default=500, help="Number of training episodes"
    )
    parser.add_argument(
        "--total-timesteps", type=int, default=100_000, help="Total training timesteps"
    )
    parser.add_argument(
        "--save-path",
        default="tools/ppo_models/simhpc_ppo_final.zip",
        help="Model save path",
    )
    parser.add_argument("--load-path", default=None, help="Load existing model")
    parser.add_argument(
        "--tensorboard-log",
        default="./tools/tensorboard/simhpc_ppo",
        help="Tensorboard log dir",
    )
    parser.add_argument("--n-envs", type=int, default=1, help="Parallel environments")
    return parser.parse_args()


async def main():
    args = parse_args()

    # Create kernel (headless mode for training)
    kernel = Kernel()

    # Create vectorized environment
    env = make_vec_env(lambda: SimHPCEnv(kernel), n_envs=args.n_envs)

    # Load or create PPO model
    if args.load_path:
        model = PPO.load(args.load_path, env=env)
        print(f"Loaded model from {args.load_path}")
    else:
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            tensorboard_log=args.tensorboard_log,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
        )

    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10_000,
        save_path="./tools/ppo_models/checkpoints/",
        name_prefix="simhpc_ppo",
    )

    print(f"Starting PPO training for {args.total_timesteps} timesteps...")
    model.learn(
        total_timesteps=args.total_timesteps,
        callback=checkpoint_callback,
        progress_bar=True,
    )

    # Save final model
    model.save(args.save_path)
    print(f"✅ Model saved to {args.save_path}")

    # Persist policy snapshot to Supabase
    await kernel.supabase_job_store.save_rl_policy_snapshot(model.policy.state_dict())
    print("✅ Policy snapshot saved to Supabase")


if __name__ == "__main__":
    asyncio.run(main())
