"""
PPO Training Script for SproutLand Environment
Uses Stable-Baselines3 PPO with MultiInputPolicy for Dict observation space.
"""

import os
import argparse
from pathlib import Path
import numpy as np

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback, CallbackList
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.logger import configure

# Import environment
from sproutland_env import SproutLandEnv
from wrappers import ActionMasking, LoggingWrapper


def make_env(rank: int = 0, seed: int = 0, render_mode: str = None, **kwargs):
    """
    Create environment function for vectorized environments.
    """
    def _init():
        env = SproutLandEnv(render_mode=render_mode, **kwargs)
        env = Monitor(env, filename=None, allow_early_resets=True)
        env = ActionMasking(env)  # Optional: mask invalid actions
        env.reset(seed=seed + rank)
        return env
    return _init


def train(
    total_timesteps: int = 1_000_000,
    n_envs: int = 4,
    learning_rate: float = 3e-4,
    use_lr_schedule: bool = True,
    n_steps: int = 2048,
    batch_size: int = 256,
    n_epochs: int = 10,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    ent_coef: float = 0.01,
    vf_coef: float = 0.5,
    clip_range: float = 0.2,
    max_grad_norm: float = 0.5,
    log_dir: str = "./logs",
    save_dir: str = "./models",
    eval_freq: int = 50000,
    n_eval_episodes: int = 10,
    checkpoint_freq: int = 100000,
    tensorboard_log: str = None,
    seed: int = 42,
    render: bool = False,
    resume: str = None,
    **env_kwargs
):
    """
    Train PPO agent on SproutLand environment.
    
    Args:
        total_timesteps: Total number of training timesteps
        n_envs: Number of parallel environments
        learning_rate: Learning rate
        n_steps: Number of steps per update
        batch_size: Batch size for training
        n_epochs: Number of training epochs per update
        gamma: Discount factor
        gae_lambda: GAE lambda parameter
        ent_coef: Entropy coefficient
        vf_coef: Value function coefficient
        clip_range: PPO clip range
        max_grad_norm: Maximum gradient norm
        log_dir: Directory for logs
        save_dir: Directory for saved models
        eval_freq: Frequency of evaluation (in timesteps)
        n_eval_episodes: Number of episodes for evaluation
        checkpoint_freq: Frequency of checkpoints (in timesteps)
        tensorboard_log: Directory for tensorboard logs
        seed: Random seed
        render: Whether to render during training (slower)
        resume: Path to model checkpoint to resume from
        **env_kwargs: Additional environment kwargs
    """
    
    # Create directories
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)
    if tensorboard_log:
        os.makedirs(tensorboard_log, exist_ok=True)
    
    # Create vectorized environment
    render_mode = "human" if render else None
    
    if n_envs == 1:
        # Single environment
        env = DummyVecEnv([make_env(0, seed, render_mode, **env_kwargs)])
    else:
        # Multiple environments (use SubprocVecEnv for faster training)
        env = SubprocVecEnv([make_env(i, seed, None, **env_kwargs) for i in range(n_envs)])
    
    # Create evaluation environment
    eval_env = DummyVecEnv([make_env(0, seed + 1000, None, **env_kwargs)])
    
    # Create or load PPO model
    if resume:
        print(f"Resuming training from: {resume}")
        model = PPO.load(resume, env=env, device="auto")
        # Update tensorboard log path for continued training
        if tensorboard_log:
            model.tensorboard_log = tensorboard_log
    else:
        # Create learning rate schedule if enabled
        # Linear schedule: start at initial_lr, decay to final_lr over total_timesteps
        if use_lr_schedule and isinstance(learning_rate, (int, float)):
            initial_lr = learning_rate
            final_lr = learning_rate * 0.1  # Decay to 10% of initial
            
            # Create linear schedule function
            def linear_schedule(progress_remaining: float) -> float:
                """
                Linear learning rate schedule.
                progress_remaining: 1.0 at start, 0.0 at end
                """
                return final_lr + (initial_lr - final_lr) * progress_remaining
            
            lr_schedule = linear_schedule
            print(f"Using learning rate schedule: {initial_lr:.2e} -> {final_lr:.2e}")
        else:
            lr_schedule = learning_rate
        
        # Create new PPO model with MultiInputPolicy (for Dict observation space)
        model = PPO(
            "MultiInputPolicy",
            env,
            learning_rate=lr_schedule,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            gae_lambda=gae_lambda,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            clip_range=clip_range,
            max_grad_norm=max_grad_norm,
            verbose=1,
            tensorboard_log=tensorboard_log,
            seed=seed,
            device="auto"  # Use GPU if available
        )
    
    # Setup callbacks
    callbacks = []
    
    # Evaluation callback
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(save_dir, "best"),
        log_path=log_dir,
        eval_freq=eval_freq,
        n_eval_episodes=n_eval_episodes,
        deterministic=True,
        render=False
    )
    callbacks.append(eval_callback)
    
    # Checkpoint callback
    checkpoint_callback = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=save_dir,
        name_prefix="ppo_sproutland"
    )
    callbacks.append(checkpoint_callback)
    
    callback_list = CallbackList(callbacks)
    
    # Train the model
    if resume:
        print(f"Continuing training for {total_timesteps} additional timesteps...")
    else:
        print(f"Starting training for {total_timesteps} timesteps...")
    print(f"Using {n_envs} parallel environments")
    print(f"Model will be saved to: {save_dir}")
    if tensorboard_log:
        print(f"Tensorboard logs: tensorboard --logdir {tensorboard_log}")
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback_list,
        progress_bar=True,
        reset_num_timesteps=not bool(resume)  # Continue timestep counter if resuming
    )
    
    # Save final model
    final_model_path = os.path.join(save_dir, "ppo_sproutland_final")
    model.save(final_model_path)
    print(f"Training complete! Final model saved to: {final_model_path}")
    
    # Close environments
    env.close()
    eval_env.close()


def main():
    parser = argparse.ArgumentParser(description="Train PPO agent on SproutLand environment")
    
    # Training parameters
    parser.add_argument("--total-timesteps", type=int, default=1_000_000, help="Total timesteps")
    parser.add_argument("--n-envs", type=int, default=4, help="Number of parallel environments")
    parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--use-lr-schedule", action="store_true", default=True, help="Use learning rate schedule")
    parser.add_argument("--no-lr-schedule", dest="use_lr_schedule", action="store_false", help="Don't use learning rate schedule")
    parser.add_argument("--n-steps", type=int, default=2048, help="Steps per update (must be <= total_timesteps)")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size")
    parser.add_argument("--n-epochs", type=int, default=10, help="Training epochs per update")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--gae-lambda", type=float, default=0.95, help="GAE lambda")
    parser.add_argument("--ent-coef", type=float, default=0.01, help="Entropy coefficient")
    
    # Directories
    parser.add_argument("--log-dir", type=str, default="./logs", help="Log directory")
    parser.add_argument("--save-dir", type=str, default="./models", help="Model save directory")
    parser.add_argument("--tensorboard-log", type=str, default="./tensorboard", help="Tensorboard log directory")
    
    # Evaluation
    parser.add_argument("--eval-freq", type=int, default=50000, help="Evaluation frequency")
    parser.add_argument("--n-eval-episodes", type=int, default=10, help="Evaluation episodes")
    parser.add_argument("--checkpoint-freq", type=int, default=100000, help="Checkpoint frequency")
    
    # Environment parameters
    parser.add_argument("--max-steps", type=int, default=10000, help="Max steps per episode")
    parser.add_argument("--max-days", type=int, default=30, help="Max days per episode")
    parser.add_argument("--frames-per-step", type=int, default=6, help="Frames per step")
    parser.add_argument("--grid-window-size", type=int, default=9, help="Grid observation window size")
    parser.add_argument("--money-target", type=float, default=None, help="Money target for success")
    
    # Resume training
    parser.add_argument("--resume", type=str, default=None, help="Path to model checkpoint to resume training from")
    
    # Other
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--render", action="store_true", help="Render during training (slower)")
    
    args = parser.parse_args()
    
    # Environment kwargs
    env_kwargs = {
        "grid_window_size": args.grid_window_size,
        "max_steps": args.max_steps,
        "max_days": args.max_days,
        "frames_per_step": args.frames_per_step,
        "money_target": args.money_target,
        "reward_config": None  # Use defaults
    }
    
    # Train
    train(
        total_timesteps=args.total_timesteps,
        n_envs=args.n_envs,
        learning_rate=args.learning_rate,
        use_lr_schedule=args.use_lr_schedule,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        n_epochs=args.n_epochs,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        ent_coef=args.ent_coef,
        log_dir=args.log_dir,
        save_dir=args.save_dir,
        eval_freq=args.eval_freq,
        n_eval_episodes=args.n_eval_episodes,
        checkpoint_freq=args.checkpoint_freq,
        tensorboard_log=args.tensorboard_log,
        seed=args.seed,
        render=args.render,
        resume=args.resume,
        **env_kwargs
    )


if __name__ == "__main__":
    main()
