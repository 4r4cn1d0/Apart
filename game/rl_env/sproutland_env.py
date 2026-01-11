"""
SproutLand RL Environment
Gymnasium-compatible environment for the Stardew Valley-style farming game.
"""

import sys
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
import pygame

# Add parent directory to path to import game code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

import gymnasium as gym
from gymnasium import spaces
from gymnasium.core import Env

# ADAPT THIS BLOCK: Import paths may need adjustment based on your project structure
try:
    from settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, SALE_PRICES, PURCHASE_PRICES
    from level import Level
except ImportError:
    # Fallback if imports fail
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from code.settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, SALE_PRICES, PURCHASE_PRICES
    from code.level import Level


@dataclass
class AgentControls:
    """Command buffer for agent actions"""
    move: int = 0  # 0=noop, 1=up, 2=down, 3=left, 4=right
    tool_action: int = 0  # 0=noop, 1=switch_tool, 2=use_tool
    seed_action: int = 0  # 0=noop, 1=switch_seed, 2=plant_seed
    interact: int = 0  # 0=noop, 1=interact
    menu_action: int = 0  # 0=noop, 1=up, 2=down, 3=select, 4=exit


class SproutLandEnv(gym.Env):
    """
    SproutLand RL Environment
    
    Action Space: MultiDiscrete(5) with branches:
    - move: [0-4] noop, up, down, left, right
    - tool_action: [0-2] noop, switch_tool, use_tool
    - seed_action: [0-2] noop, switch_seed, plant_seed
    - interact: [0-1] noop, interact
    - menu_action: [0-4] noop, up, down, select, exit
    """
    
    metadata = {"render_modes": ["human", "none"], "render_fps": 60}
    
    def __init__(
        self,
        render_mode: Optional[str] = None,
        grid_window_size: int = 9,
        max_steps: int = 10000,
        max_days: int = 30,
        frames_per_step: int = 6,
        fixed_dt: float = 1.0 / 60.0,
        money_target: Optional[float] = None,
        reward_config: Optional[Dict] = None
    ):
        super().__init__()
        
        self.render_mode = render_mode
        self.grid_window_size = grid_window_size
        self.max_steps = max_steps
        self.max_days = max_days
        self.frames_per_step = frames_per_step
        self.fixed_dt = fixed_dt
        self.money_target = money_target
        
        # Reward configuration
        default_reward_config = {
            'step_penalty': -0.001,
            'money_scale': 0.05,  # Increased from 0.02 - bigger reward for selling
            'spend_penalty_scale': 0.005,
            'harvest_bonus': 0.75,  # Increased from 0.5
            'till_success': 0.15,  # Increased from 0.1
            'water_success': 0.15,  # Increased from 0.1
            'plant_success': 0.15,  # Increased from 0.1
            'invalid_action_penalty': -0.01,
            'repeat_action_penalty': -0.05,  # Penalty for repeating same action in same spot
            'sequence_bonus': 0.5,  # Increased from 0.3 - bigger reward for correct sequences
            'cycle_completion_bonus': 2.0,  # Increased from 1.0 - much bigger reward for completing cycle
            'sell_bonus': 0.5,  # NEW: Bonus for selling crops
            'cycle_count_bonus': 0.2,  # NEW: Bonus per cycle completed (scales with cycle count)
            'stuck_penalty': -0.02,  # Penalty for being stuck (not moving position)
            'repetitive_movement_penalty': -0.03  # Penalty for repeating same movement action many times
        }
        self.reward_config = {**default_reward_config, **(reward_config or {})}
        
        # Initialize pygame
        # For headless mode, set dummy driver before init
        if render_mode != "human":
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        if render_mode == "human":
            pygame.display.set_caption('SproutLand RL')
            self.clock = pygame.time.Clock()
        else:
            # Headless mode - display surface created but not visible
            pass
        
        # Action space: MultiDiscrete with 5 branches
        self.action_space = spaces.MultiDiscrete([5, 3, 3, 2, 5])
        
        # Observation space: Dict with player state and grid
        player_state_size = (
            2 +  # tile coords (x, y)
            4 +  # facing direction one-hot
            3 +  # selected tool one-hot
            2 +  # selected seed one-hot
            1 +  # raining (0/1)
            1 +  # shop_active (0/1)
            1 +  # money (normalized)
            4 +  # item inventory counts (normalized)
            2    # seed inventory counts (normalized)
        )  # Total: 20
        
        # Grid observation: (W, W, C) where C = 5 channels (farmable, tilled, watered, planted, plant_type/growth)
        grid_channels = 5  # farmable, tilled, watered, planted, plant_type_norm
        self.observation_space = spaces.Dict({
            "player": spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(player_state_size,),
                dtype=np.float32
            ),
            "grid": spaces.Box(
                low=0.0,
                high=1.0,
                shape=(grid_window_size, grid_window_size, grid_channels),
                dtype=np.float32
            )
        })
        
        # Internal state
        self.level = None
        self.step_count = 0
        self.day_count = 0
        self.prev_money = 0
        self.events = []  # Event list for reward computation
        self.prev_day_count = 0
        
        # Action tracking for penalties and sequence rewards
        self.last_action_type = None  # 'till', 'water', 'plant', or None
        self.last_action_tile = None  # (tile_x, tile_y) tuple
        self.last_action_step = -1  # Step count when last action occurred
        self.cycle_progress = []  # Track cycle progress: ['till', 'plant', 'water'] -> harvest completes cycle
        self.cycles_completed = 0  # Track total cycles completed
        self.last_harvest_step = -1  # Track when last harvest occurred
        
        # Movement tracking for stuck behavior detection
        self.recent_moves = []  # Track last N movement actions
        self.prev_player_pos = None  # Previous player position (tile coordinates)
        self.same_move_count = 0  # Count of consecutive same movement actions
        self.stuck_step_count = 0  # Count of steps without position change
        
        # Agent controls
        self.agent_controls = AgentControls()
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None):
        """Reset the environment"""
        super().reset(seed=seed)
        
        # Reset internal state
        self.step_count = 0
        self.day_count = 0
        self.prev_day_count = 0
        self.events = []
        
        # Reset action tracking
        self.last_action_type = None
        self.last_action_tile = None
        self.last_action_step = -1
        self.cycle_progress = []
        self.cycles_completed = 0
        self.last_harvest_step = -1
        
        # Reset movement tracking
        self.recent_moves = []
        self.prev_player_pos = None
        self.same_move_count = 0
        self.stuck_step_count = 0
        
        # ADAPT THIS BLOCK: Create Level instance
        # The Level class needs to be modified to accept use_agent_controls parameter
        # For now, we'll set it after creation (see integration patch)
        self.level = Level()
        self.level.use_agent_controls = True
        self.level.agent_controls = self.agent_controls
        self.level.env_events = self.events  # For event collection
        
        # ADAPT THIS BLOCK: Set player's agent controls reference
        if hasattr(self.level, 'player'):
            self.level.player.use_agent_controls = True
            self.level.player.agent_controls = self.agent_controls
        
        # Initialize player state tracking
        self.prev_money = self.level.player.money
        
        # Run initial frame to stabilize
        for _ in range(self.frames_per_step):
            self._step_simulation()
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action):
        """Execute one step in the environment"""
        # Parse action
        move_action, tool_action, seed_action, interact_action, menu_action = action
        
        # Track movement actions for stuck detection
        # Only track non-noop movement actions (1=up, 2=down, 3=left, 4=right)
        if move_action > 0:
            if len(self.recent_moves) > 0 and self.recent_moves[-1] == move_action:
                self.same_move_count += 1
            else:
                self.same_move_count = 1
            # Keep only last 20 moves for tracking
            self.recent_moves.append(move_action)
            if len(self.recent_moves) > 20:
                self.recent_moves.pop(0)
        else:
            # Reset count on noop
            self.same_move_count = 0
        
        # Clear events from previous step
        self.events.clear()
        
        # Set agent controls (will be consumed by player/level)
        self.agent_controls.move = move_action
        self.agent_controls.tool_action = tool_action
        self.agent_controls.seed_action = seed_action
        self.agent_controls.interact = interact_action
        self.agent_controls.menu_action = menu_action
        
        # Track day changes
        self.prev_day_count = self.day_count
        if hasattr(self.level, 'day_count'):
            self.day_count = self.level.day_count
        
        # Advance simulation for frames_per_step frames
        for _ in range(self.frames_per_step):
            self._step_simulation()
        
        # Get observation
        observation = self._get_observation()
        
        # Compute reward
        reward = self._compute_reward()
        
        # Check termination conditions
        terminated = False
        truncated = False
        
        # Success condition (optional)
        if self.money_target and self.level.player.money >= self.money_target:
            terminated = True
        
        # Truncation conditions
        if self.step_count >= self.max_steps:
            truncated = True
        
        if self.day_count >= self.max_days:
            truncated = True
        
        self.step_count += 1
        
        # Update previous state
        self.prev_money = self.level.player.money
        
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _step_simulation(self):
        """Run one simulation frame with fixed dt"""
        # Handle pygame events (for window close, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Can handle quit if needed
        
        # ADAPT THIS BLOCK: Call level.run with fixed dt
        # The level.run() method should use agent controls if use_agent_controls is True
        self.level.run(self.fixed_dt)
        
        # Update display if rendering
        if self.render_mode == "human":
            pygame.display.update()
            self.clock.tick(self.metadata["render_fps"])
    
    def _get_observation(self) -> Dict[str, np.ndarray]:
        """Extract observation from game state"""
        player = self.level.player
        soil_layer = self.level.soil_layer
        
        # Player tile coordinates
        player_tile_x = int(player.pos.x) // TILE_SIZE
        player_tile_y = int(player.pos.y) // TILE_SIZE
        
        # Facing direction one-hot (extract from status: 'up', 'down', 'left', 'right')
        direction_str = player.status.split('_')[0]
        direction_map = {'up': 0, 'down': 1, 'left': 2, 'right': 3}
        facing_onehot = np.zeros(4, dtype=np.float32)
        facing_onehot[direction_map.get(direction_str, 1)] = 1.0
        
        # Selected tool one-hot
        tool_map = {'hoe': 0, 'axe': 1, 'water': 2}
        tool_onehot = np.zeros(3, dtype=np.float32)
        tool_onehot[tool_map.get(player.selected_tool, 0)] = 1.0
        
        # Selected seed one-hot
        seed_map = {'corn': 0, 'tomato': 1}
        seed_onehot = np.zeros(2, dtype=np.float32)
        seed_onehot[seed_map.get(player.selected_seed, 0)] = 1.0
        
        # Other player state
        raining = 1.0 if self.level.raining else 0.0
        shop_active = 1.0 if self.level.shop_active else 0.0
        
        # Normalize money (assuming max around 10000, adjust if needed)
        money_norm = min(player.money / 10000.0, 1.0)
        
        # Normalize inventory (assuming max around 100, adjust if needed)
        item_inv = np.array([
            min(player.item_inventory['wood'] / 100.0, 1.0),
            min(player.item_inventory['apple'] / 100.0, 1.0),
            min(player.item_inventory['corn'] / 100.0, 1.0),
            min(player.item_inventory['tomato'] / 100.0, 1.0),
        ], dtype=np.float32)
        
        seed_inv = np.array([
            min(player.seed_inventory['corn'] / 100.0, 1.0),
            min(player.seed_inventory['tomato'] / 100.0, 1.0),
        ], dtype=np.float32)
        
        # Build player state vector
        player_state = np.concatenate([
            [player_tile_x, player_tile_y],
            facing_onehot,
            tool_onehot,
            seed_onehot,
            [raining, shop_active, money_norm],
            item_inv,
            seed_inv
        ], dtype=np.float32)
        
        # Grid observation (local window around player)
        grid_obs = self._get_grid_observation(player_tile_x, player_tile_y)
        
        return {
            "player": player_state,
            "grid": grid_obs
        }
    
    def _get_grid_observation(self, center_x: int, center_y: int) -> np.ndarray:
        """Extract local grid window around player"""
        window_size = self.grid_window_size
        half_window = window_size // 2
        
        # Initialize grid tensor: (W, W, 5)
        # Channels: farmable, tilled, watered, planted, plant_type_norm
        grid = np.zeros((window_size, window_size, 5), dtype=np.float32)
        
        # ADAPT THIS BLOCK: Access soil_layer.grid
        # Create plant lookup dict for efficiency
        plant_lookup = {}
        for plant in self.level.soil_layer.plant_sprites.sprites():
            tx = int(plant.rect.centerx) // TILE_SIZE
            ty = int(plant.rect.centery) // TILE_SIZE
            plant_lookup[(tx, ty)] = plant
        
        # Fill grid window
        for dy in range(-half_window, half_window + 1):
            for dx in range(-half_window, half_window + 1):
                tx = center_x + dx
                ty = center_y + dy
                
                # Grid indices (0 to window_size-1)
                gx = dx + half_window
                gy = dy + half_window
                
                # Check bounds
                if (0 <= ty < len(self.level.soil_layer.grid) and
                    0 <= tx < len(self.level.soil_layer.grid[0])):
                    
                    cell = self.level.soil_layer.grid[ty][tx]
                    
                    # Channel 0: Farmable
                    if 'F' in cell:
                        grid[gy, gx, 0] = 1.0
                    
                    # Channel 1: Tilled
                    if 'X' in cell:
                        grid[gy, gx, 1] = 1.0
                    
                    # Channel 2: Watered
                    if 'W' in cell:
                        grid[gy, gx, 2] = 1.0
                    
                    # Channel 3: Planted
                    if 'P' in cell:
                        grid[gy, gx, 3] = 1.0
                        
                        # Channel 4: Plant type and growth stage (normalized)
                        if (tx, ty) in plant_lookup:
                            plant = plant_lookup[(tx, ty)]
                            # Encode type: corn=0.5, tomato=1.0, scaled by growth
                            type_val = 0.5 if plant.plant_type == 'corn' else 1.0
                            growth_norm = min(plant.age / plant.max_age, 1.0) if plant.max_age > 0 else 0.0
                            grid[gy, gx, 4] = type_val * growth_norm
                    else:
                        grid[gy, gx, 4] = 0.0
                # Out of bounds: all zeros (already initialized)
        
        return grid
    
    def _get_target_tile(self) -> Optional[Tuple[int, int]]:
        """Get the target tile coordinates based on player position and facing direction"""
        try:
            player = self.level.player
            # Calculate target position (same as in player.get_target_pos())
            from settings import PLAYER_TOOL_OFFSET
            facing_dir = player.status.split('_')[0]
            if facing_dir in PLAYER_TOOL_OFFSET:
                target_pos = player.rect.center + PLAYER_TOOL_OFFSET[facing_dir]
                tile_x = int(target_pos.x) // TILE_SIZE
                tile_y = int(target_pos.y) // TILE_SIZE
                return (tile_x, tile_y)
        except:
            pass
        return None
    
    def _compute_reward(self) -> float:
        """Compute reward based on events and state changes"""
        reward = 0.0
        
        # Step penalty (reduced when actively farming)
        base_step_penalty = self.reward_config['step_penalty']
        # Reduce penalty if we're in the middle of a cycle
        if len(self.cycle_progress) > 0:
            base_step_penalty *= 0.5  # Half penalty during farming
        reward += base_step_penalty
        
        # Money delta (profit)
        money_delta = self.level.player.money - self.prev_money
        reward += self.reward_config['money_scale'] * money_delta
        
        # Bonus for selling crops (detected via money increase)
        # Only give bonus if money increased and we recently harvested
        if money_delta > 0:
            # Check if this is likely a crop sale (corn=$10, tomato=$20)
            # Give bonus if we sold crops recently after harvest
            if (self.last_harvest_step >= 0 and 
                self.step_count - self.last_harvest_step < 100):  # Sold within 100 steps of harvest
                # Additional bonus for selling crops
                if money_delta >= 10:  # Likely sold a crop
                    reward += self.reward_config['sell_bonus']
        
        # Spending penalty (optional)
        if money_delta < 0:
            reward += self.reward_config['spend_penalty_scale'] * abs(money_delta)
        
        # Penalty for repetitive movement (stuck in same direction)
        if self.same_move_count >= 10:  # If same movement action repeated 10+ times
            reward += self.reward_config['repetitive_movement_penalty']
        
        # Penalty for being stuck (not moving position)
        try:
            player = self.level.player
            current_pos = (int(player.pos.x) // TILE_SIZE, int(player.pos.y) // TILE_SIZE)
            if self.prev_player_pos is not None:
                if current_pos == self.prev_player_pos:
                    self.stuck_step_count += 1
                    # If stuck for more than 20 steps, apply penalty
                    if self.stuck_step_count > 20:
                        reward += self.reward_config['stuck_penalty']
                else:
                    self.stuck_step_count = 0
            self.prev_player_pos = current_pos
        except:
            pass
        
        # Event-based rewards with action tracking
        # ADAPT THIS BLOCK: Events should be populated by game code
        # See integration patches for player.py and level.py
        for event in self.events:
            if event == 'harvest':
                reward += self.reward_config['harvest_bonus']
                
                # Check for cycle completion: till->plant->water->harvest
                cycle_completed = False
                if len(self.cycle_progress) >= 3:
                    # Check if last 3 actions were till, plant, water (in any order but all present)
                    recent_actions = self.cycle_progress[-3:]
                    if set(recent_actions) == {'till', 'plant', 'water'}:
                        reward += self.reward_config['cycle_completion_bonus']
                        cycle_completed = True
                        self.cycles_completed += 1
                        # Bonus for completing multiple cycles (encourages more cycles)
                        if self.cycles_completed > 0:
                            reward += self.reward_config['cycle_count_bonus'] * min(self.cycles_completed, 10)
                
                # Reset action tracking after harvest (cycle complete)
                self.last_action_type = None
                self.last_action_tile = None
                self.cycle_progress = []
                self.last_harvest_step = self.step_count
            elif event == 'till_success':
                reward += self.reward_config['till_success']
                current_action_tile = self._get_target_tile()
                
                # Bonus for starting a new cycle after completing one
                if (self.last_harvest_step >= 0 and 
                    self.step_count - self.last_harvest_step < 200):  # Started new cycle soon after harvest
                    reward += 0.1  # Small bonus for being proactive
                
                # Check for repeated action in same spot
                if (self.last_action_type == 'till' and 
                    current_action_tile and 
                    current_action_tile == self.last_action_tile):
                    reward += self.reward_config['repeat_action_penalty']
                
                # Update tracking
                self.last_action_type = 'till'
                self.last_action_tile = current_action_tile
                self.last_action_step = self.step_count
                self.cycle_progress.append('till')
                # Keep only last 10 actions for cycle tracking
                if len(self.cycle_progress) > 10:
                    self.cycle_progress.pop(0)
                
            elif event == 'water_success':
                reward += self.reward_config['water_success']
                current_action_tile = self._get_target_tile()
                
                # Check for repeated action in same spot
                if (self.last_action_type == 'water' and 
                    current_action_tile and 
                    current_action_tile == self.last_action_tile):
                    reward += self.reward_config['repeat_action_penalty']
                
                # Check for correct sequence (plant -> water is correct!)
                if self.last_action_type == 'plant':
                    reward += self.reward_config['sequence_bonus']
                
                # Update tracking
                self.last_action_type = 'water'
                self.last_action_tile = current_action_tile
                self.last_action_step = self.step_count
                self.cycle_progress.append('water')
                # Keep only last 10 actions for cycle tracking
                if len(self.cycle_progress) > 10:
                    self.cycle_progress.pop(0)
                
            elif event == 'plant_success':
                reward += self.reward_config['plant_success']
                current_action_tile = self._get_target_tile()
                
                # Check for repeated action in same spot
                if (self.last_action_type == 'plant' and 
                    current_action_tile and 
                    current_action_tile == self.last_action_tile):
                    reward += self.reward_config['repeat_action_penalty']
                
                # Check for correct sequence (till -> plant is correct!)
                if self.last_action_type == 'till':
                    reward += self.reward_config['sequence_bonus']
                
                # Update tracking
                self.last_action_type = 'plant'
                self.last_action_tile = current_action_tile
                self.last_action_step = self.step_count
                self.cycle_progress.append('plant')
                # Keep only last 10 actions for cycle tracking
                if len(self.cycle_progress) > 10:
                    self.cycle_progress.pop(0)
                
            elif event == 'invalid_action':
                reward += self.reward_config['invalid_action_penalty']
        
        return reward
    
    def _get_info(self) -> Dict:
        """Get info dictionary"""
        return {
            'step': self.step_count,
            'day': self.day_count,
            'money': self.level.player.money,
            'events': list(self.events)
        }
    
    def render(self):
        """Render the environment"""
        if self.render_mode == "human":
            # Rendering is handled in _step_simulation
            pass
    
    def close(self):
        """Clean up resources"""
        if self.level is not None:
            # Clean up if needed
            pass
        if self.render_mode == "human":
            pygame.quit()
