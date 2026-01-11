"""
Evaluation script for trained SproutLand PPO model
Loads a trained model and runs evaluation episodes, optionally with rendering.
"""

import os
import argparse
import numpy as np
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

from sproutland_env import SproutLandEnv
from wrappers import ActionMasking


def evaluate_model(
    model_path: str,
    n_episodes: int = 10,
    render: bool = True,
    deterministic: bool = True,
    max_episode_steps: int = None,
    **env_kwargs
):
    """
    Evaluate a trained PPO model on SproutLand environment.
    
    Args:
        model_path: Path to saved model
        n_episodes: Number of episodes to run
        render: Whether to render episodes
        deterministic: Whether to use deterministic actions
        max_episode_steps: Maximum steps per episode (None = use env default)
        **env_kwargs: Additional environment kwargs
    """
    
    # Create environment
    render_mode = "human" if render else None
    env = SproutLandEnv(render_mode=render_mode, **env_kwargs)
    env = ActionMasking(env)  # Optional: mask invalid actions
    
    # Load model
    print(f"Loading model from: {model_path}")
    model = PPO.load(model_path, env=env)
    
    # Evaluate
    print(f"Evaluating model for {n_episodes} episodes...")
    print(f"Deterministic: {deterministic}, Render: {render}")
    
    episode_rewards = []
    episode_lengths = []
    episode_money = []
    episode_days = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        done = False
        episode_reward = 0.0
        episode_steps = 0
        
        while not done:
            # Get action from model
            action, _ = model.predict(obs, deterministic=deterministic)
            
            # Step environment
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            episode_reward += reward
            episode_steps += 1
            
            # Check max steps
            if max_episode_steps and episode_steps >= max_episode_steps:
                done = True
        
        # Get final stats
        final_money = env.level.player.money
        final_day = info.get('day', 0)
        
        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_steps)
        episode_money.append(final_money)
        episode_days.append(final_day)
        
        print(f"Episode {episode + 1}/{n_episodes}: "
              f"Reward: {episode_reward:.2f}, "
              f"Steps: {episode_steps}, "
              f"Money: ${final_money:.2f}, "
              f"Days: {final_day}")
    
    # Statistics
    print("\n" + "="*50)
    print("Evaluation Results:")
    print("="*50)
    print(f"Episodes: {n_episodes}")
    print(f"Mean Reward: {np.mean(episode_rewards):.2f} ± {np.std(episode_rewards):.2f}")
    print(f"Mean Episode Length: {np.mean(episode_lengths):.1f} ± {np.std(episode_lengths):.1f}")
    print(f"Mean Final Money: ${np.mean(episode_money):.2f} ± ${np.std(episode_money):.2f}")
    print(f"Mean Final Days: {np.mean(episode_days):.1f} ± {np.std(episode_days):.1f}")
    print(f"Max Reward: {np.max(episode_rewards):.2f}")
    print(f"Max Money: ${np.max(episode_money):.2f}")
    print("="*50)
    
    env.close()
    
    return {
        'rewards': episode_rewards,
        'lengths': episode_lengths,
        'money': episode_money,
        'days': episode_days
    }


def run_single_episode(
    model_path: str,
    render: bool = True,
    deterministic: bool = False,
    seed: int = None,
    **env_kwargs
):
    """
    Run a single episode interactively.
    
    Args:
        model_path: Path to saved model
        render: Whether to render
        deterministic: Whether to use deterministic actions
        seed: Random seed
        **env_kwargs: Additional environment kwargs
    """
    
    # Create environment
    render_mode = "human" if render else None
    env = SproutLandEnv(render_mode=render_mode, **env_kwargs)
    env = ActionMasking(env)
    
    # Load model
    print(f"Loading model from: {model_path}")
    model = PPO.load(model_path, env=env)
    
    # Reset
    obs, info = env.reset(seed=seed)
    done = False
    total_reward = 0.0
    step_count = 0
    
    print("Running episode (press Ctrl+C to stop)...")
    
    try:
        while not done:
            # Get action
            action, _ = model.predict(obs, deterministic=deterministic)
            
            # Step
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward
            step_count += 1
            
            # Print periodic updates
            if step_count % 100 == 0:
                money = env.level.player.money
                day = info.get('day', 0)
                print(f"Step {step_count}: Reward: {total_reward:.2f}, Money: ${money:.2f}, Day: {day}")
    
    except KeyboardInterrupt:
        print("\nEpisode interrupted by user")
    
    # Final stats
    final_money = env.level.player.money
    final_day = info.get('day', 0)
    
    print("\n" + "="*50)
    print("Episode Complete:")
    print("="*50)
    print(f"Total Reward: {total_reward:.2f}")
    print(f"Total Steps: {step_count}")
    print(f"Final Money: ${final_money:.2f}")
    print(f"Final Day: {final_day}")
    print("="*50)
    
    env.close()


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained SproutLand PPO model")
    
    parser.add_argument("model_path", type=str, help="Path to saved model")
    parser.add_argument("--n-episodes", type=int, default=10, help="Number of evaluation episodes")
    parser.add_argument("--render", action="store_true", help="Render episodes")
    parser.add_argument("--no-render", dest="render", action="store_false", help="Don't render (faster)")
    parser.set_defaults(render=True)
    parser.add_argument("--deterministic", action="store_true", default=True, help="Use deterministic actions")
    parser.add_argument("--stochastic", dest="deterministic", action="store_false", help="Use stochastic actions")
    parser.add_argument("--single", action="store_true", help="Run single interactive episode")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--max-episode-steps", type=int, default=None, help="Max steps per episode")
    
    # Environment parameters
    parser.add_argument("--max-steps", type=int, default=10000, help="Max steps per episode")
    parser.add_argument("--max-days", type=int, default=30, help="Max days per episode")
    parser.add_argument("--frames-per-step", type=int, default=6, help="Frames per step")
    parser.add_argument("--grid-window-size", type=int, default=9, help="Grid observation window size")
    
    args = parser.parse_args()
    
    # Environment kwargs
    env_kwargs = {
        "grid_window_size": args.grid_window_size,
        "max_steps": args.max_steps,
        "max_days": args.max_days,
        "frames_per_step": args.frames_per_step,
        "money_target": None,
        "reward_config": None
    }
    
    # Run evaluation
    if args.single:
        run_single_episode(
            args.model_path,
            render=args.render,
            deterministic=args.deterministic,
            seed=args.seed,
            **env_kwargs
        )
    else:
        evaluate_model(
            args.model_path,
            n_episodes=args.n_episodes,
            render=args.render,
            deterministic=args.deterministic,
            max_episode_steps=args.max_episode_steps,
            **env_kwargs
        )


if __name__ == "__main__":
    main()
