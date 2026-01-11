"""
Optional wrappers for SproutLand environment
Includes normalization, action masking, action adapter, and logging wrappers.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Any, Optional


class NormalizeObservation(gym.ObservationWrapper):
    """Normalize observation space to [-1, 1] range"""
    
    def __init__(self, env):
        super().__init__(env)
        
        # Compute normalization bounds
        self.obs_low = {}
        self.obs_high = {}
        self.obs_scale = {}
        
        for key, space in env.observation_space.spaces.items():
            if isinstance(space, spaces.Box):
                # For player state, we'll normalize based on expected ranges
                if key == "player":
                    # Approximate bounds (adjust based on actual game ranges)
                    # tile coords: 0-100, one-hots: 0-1, normalized values: 0-1
                    low = np.array([
                        -10.0, -10.0,  # tile coords (allow negative for padding)
                        0.0, 0.0, 0.0, 0.0,  # facing one-hot
                        0.0, 0.0, 0.0,  # tool one-hot
                        0.0, 0.0,  # seed one-hot
                        0.0, 0.0, 0.0,  # raining, shop_active, money_norm
                        0.0, 0.0, 0.0, 0.0,  # item inventory
                        0.0, 0.0  # seed inventory
                    ], dtype=np.float32)
                    high = np.array([
                        200.0, 200.0,  # tile coords
                        1.0, 1.0, 1.0, 1.0,  # facing one-hot
                        1.0, 1.0, 1.0,  # tool one-hot
                        1.0, 1.0,  # seed one-hot
                        1.0, 1.0, 1.0,  # raining, shop_active, money_norm
                        1.0, 1.0, 1.0, 1.0,  # item inventory
                        1.0, 1.0  # seed inventory
                    ], dtype=np.float32)
                elif key == "grid":
                    low = np.zeros(space.shape, dtype=np.float32)
                    high = np.ones(space.shape, dtype=np.float32)
                else:
                    low = space.low
                    high = space.high
                
                self.obs_low[key] = low
                self.obs_high[key] = high
                self.obs_scale[key] = high - low
                self.obs_scale[key][self.obs_scale[key] == 0] = 1.0  # Avoid division by zero
    
    def observation(self, obs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Normalize observation"""
        normalized_obs = {}
        for key, value in obs.items():
            if key in self.obs_scale:
                # Normalize to [-1, 1]
                normalized = 2.0 * (value - self.obs_low[key]) / self.obs_scale[key] - 1.0
                normalized_obs[key] = normalized.astype(np.float32)
            else:
                normalized_obs[key] = value
        return normalized_obs


class ActionMasking(gym.ActionWrapper):
    """
    Mask invalid actions based on game state.
    Rules:
    - If shop_active: only menu_action valid (others masked)
    - If not shop_active: menu_action masked (others valid)
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.action_space = env.action_space  # Keep MultiDiscrete
    
    def action(self, action):
        """Mask invalid actions"""
        # ADAPT THIS BLOCK: Access shop_active state
        # This requires access to env.level.shop_active
        shop_active = self.env.unwrapped.level.shop_active if hasattr(self.env.unwrapped, 'level') and self.env.unwrapped.level else False
        
        move_action, tool_action, seed_action, interact_action, menu_action = action
        
        if shop_active:
            # In shop: only menu actions valid, others set to noop
            return np.array([0, 0, 0, 0, menu_action], dtype=self.action_space.dtype)
        else:
            # Not in shop: menu actions set to noop
            return np.array([move_action, tool_action, seed_action, interact_action, 0], dtype=self.action_space.dtype)


class ActionAdapter(gym.ActionWrapper):
    """
    Adapt actions to game's internal representation.
    Currently just passes through, but can be extended for action remapping.
    """
    
    def __init__(self, env):
        super().__init__(env)
    
    def action(self, action):
        """Adapter can transform actions if needed"""
        return action


class LoggingWrapper(gym.Wrapper):
    """Log environment statistics"""
    
    def __init__(self, env, log_interval: int = 100):
        super().__init__(env)
        self.log_interval = log_interval
        self.episode_count = 0
        self.step_count = 0
        self.total_reward = 0.0
        self.episode_rewards = []
        self.episode_lengths = []
    
    def reset(self, **kwargs):
        """Reset with logging"""
        if self.episode_count > 0:
            self.episode_rewards.append(self.total_reward)
            self.episode_lengths.append(self.step_count)
            
            if self.episode_count % self.log_interval == 0:
                avg_reward = np.mean(self.episode_rewards[-self.log_interval:])
                avg_length = np.mean(self.episode_lengths[-self.log_interval:])
                print(f"Episode {self.episode_count}: Avg Reward: {avg_reward:.2f}, Avg Length: {avg_length:.1f}")
        
        obs, info = self.env.reset(**kwargs)
        self.episode_count += 1
        self.step_count = 0
        self.total_reward = 0.0
        return obs, info
    
    def step(self, action):
        """Step with logging"""
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.step_count += 1
        self.total_reward += reward
        return obs, reward, terminated, truncated, info
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        if len(self.episode_rewards) == 0:
            return {}
        return {
            'episode_count': self.episode_count,
            'avg_reward': np.mean(self.episode_rewards),
            'std_reward': np.std(self.episode_rewards),
            'avg_length': np.mean(self.episode_lengths),
            'std_length': np.std(self.episode_lengths),
        }
