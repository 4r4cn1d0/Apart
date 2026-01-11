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
                    # Player state size is now 25 elements (Phase 2 additions)
                    low = np.array([
                        -10.0, -10.0,  # tile coords (allow negative for padding)
                        0.0, 0.0, 0.0, 0.0,  # facing one-hot
                        0.0, 0.0, 0.0,  # tool one-hot
                        0.0, 0.0,  # seed one-hot
                        0.0, 0.0, 0.0,  # raining, shop_active, money_norm
                        0.0, 0.0, 0.0, 0.0,  # item inventory
                        0.0, 0.0,  # seed inventory
                        # Phase 2 additions:
                        0.0,  # day_progress
                        0.0,  # distance_to_trader
                        0.0,  # distance_to_harvestable
                        0.0,  # crops_per_day
                        0.0   # money_per_step
                    ], dtype=np.float32)
                    high = np.array([
                        200.0, 200.0,  # tile coords
                        1.0, 1.0, 1.0, 1.0,  # facing one-hot
                        1.0, 1.0, 1.0,  # tool one-hot
                        1.0, 1.0,  # seed one-hot
                        1.0, 1.0, 1.0,  # raining, shop_active, money_norm
                        1.0, 1.0, 1.0, 1.0,  # item inventory
                        1.0, 1.0,  # seed inventory
                        # Phase 2 additions:
                        1.0,  # day_progress
                        1.0,  # distance_to_trader
                        1.0,  # distance_to_harvestable
                        1.0,  # crops_per_day
                        1.0   # money_per_step
                    ], dtype=np.float32)
                elif key == "grid":
                    low = np.zeros(space.shape, dtype=np.float32)
                    high = np.ones(space.shape, dtype=np.float32)
                elif key == "action_history":
                    # Action history is already normalized to [0, 1]
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
    - If seed inventory is 0: mask seed planting (seed_action=2)
    - Mask tool/seed actions when their cooldown timers are active
    - Enhanced shop masking based on player inventory and money
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.action_space = env.action_space  # Keep MultiDiscrete
    
    def action(self, action):
        """Mask invalid actions"""
        # Access game state through unwrapped env
        level = self.env.unwrapped.level if hasattr(self.env.unwrapped, 'level') else None
        shop_active = level.shop_active if level else False
        
        move_action, tool_action, seed_action, interact_action, menu_action = action
        
        if shop_active:
            # In shop: only menu actions valid, others set to noop
            masked_action = np.array([0, 0, 0, 0, menu_action], dtype=self.action_space.dtype)
        else:
            # Not in shop: menu actions set to noop
            masked_action = np.array([move_action, tool_action, seed_action, interact_action, 0], dtype=self.action_space.dtype)
            
            if level and hasattr(level, 'player'):
                player = level.player
                
                # Mask tool actions when cooldown is active
                if player.timers['tool use'].active:
                    # Tool use is on cooldown - mask tool use action
                    if masked_action[1] == 2:  # use_tool
                        masked_action[1] = 0  # Set to noop
                
                if player.timers['tool switch'].active:
                    # Tool switch is on cooldown - mask tool switch action
                    if masked_action[1] == 1:  # switch_tool
                        masked_action[1] = 0  # Set to noop
                
                # Mask seed actions when cooldown is active
                if player.timers['seed use'].active:
                    # Seed use is on cooldown - mask seed planting
                    if masked_action[2] == 2:  # plant_seed
                        masked_action[2] = 0  # Set to noop
                
                if player.timers['seed switch'].active:
                    # Seed switch is on cooldown - mask seed switch
                    if masked_action[2] == 1:  # switch_seed
                        masked_action[2] = 0  # Set to noop
                
                # Phase 4: Mask seed planting when inventory is 0
                selected_seed = player.selected_seed
                seed_count = player.seed_inventory.get(selected_seed, 0)
                
                # If trying to plant (seed_action=2) with no seeds, mask to noop
                if masked_action[2] == 2 and seed_count == 0:
                    masked_action[2] = 0  # Set seed_action to noop
        
        return masked_action


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
