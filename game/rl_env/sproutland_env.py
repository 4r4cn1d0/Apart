"""
SproutLand RL Environment
Gymnasium-compatible environment for the Stardew Valley-style farming game.
"""

import sys
import os
from collections import deque
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
        reward_config: Optional[Dict] = None,
        action_history_size: int = 5  # Phase 2: Number of past actions to track
    ):
        super().__init__()
        
        self.render_mode = render_mode
        self.grid_window_size = grid_window_size
        self.max_steps = max_steps
        self.max_days = max_days
        self.frames_per_step = frames_per_step
        self.fixed_dt = fixed_dt
        self.money_target = money_target
        self.action_history_size = action_history_size
        
        # Reward configuration
        # Comprehensive cycle-based reward system
        default_reward_config = {
            # Base penalties
            'step_penalty': -0.001,  # Small penalty per step to encourage efficiency
            
            # Money-based rewards (scaled by actual profit)
            'money_scale': 0.05,  # Reward for money earned (5% of money delta)
            'spend_penalty_scale': 0.01,  # Small penalty for spending (to encourage selling first)
            'profit_bonus_scale': 0.1,  # Bonus for actual profit (sale - purchase)
            
            # Individual action rewards (small - cycle completion is the main reward)
            'till_success': 0.1,  # Reward for tilling (part of cycle)
            'water_success': 0.1,  # Reward for watering (part of cycle)
            'plant_success': 0.1,  # Reward for planting (part of cycle)
            'harvest_bonus': 0.5,  # Reward for harvesting (part of cycle)
            
            # Complete farming cycle rewards (MAJOR REWARDS)
            'cycle_completion_bonus': 5.0,  # HUGE reward for completing full cycle (till→water→plant→harvest)
            'cycle_efficiency_bonus': 2.0,  # Bonus for completing cycle quickly (< 200 steps)
            'cycle_profit_bonus_scale': 0.2,  # Additional bonus based on profit from cycle
            
            # Incomplete cycle penalties (discourage starting cycles without finishing)
            'incomplete_cycle_penalty': -1.0,  # Penalty for abandoning a cycle
            'cycle_abandonment_threshold': 500,  # Steps before cycle is considered abandoned
            
            # Action spam penalties
            'invalid_action_penalty': -0.1,  # Heavy penalty for invalid actions
            'action_spam_penalty': -0.05,  # Penalty for actions during cooldown (detected by no events)
            
            # Selling and buying rewards
            'sell_bonus': 0.2,  # Reward for selling items (encourages selling crops)
            'sell_profit_bonus_scale': 0.15,  # Bonus based on profit from sale
            'buy_seed_bonus': 0.05,  # Small reward for buying seeds
            'low_seed_purchase_bonus': 0.3,  # Bonus for buying when inventory is low (< 3)
            
            # Resource collection
            'apple_collect_bonus': 0.1,
            'wood_collect_bonus': 0.2,
            
            # Crop diversity and preferences
            'diversity_bonus': 1.0,  # Reward for growing both corn and tomato
            'tomato_preference_bonus': 0.1,  # Small bonus for tomato (higher value)
            'tomato_seed_purchase_bonus': 0.1,  # Bonus for buying tomato seeds
            
            # Day and efficiency
            'day_complete_bonus': 0.5,  # Reward for completing a day
            'idle_penalty_threshold': 50,  # Steps before idle penalty (reduced from 100)
            'idle_penalty_scale': -0.002,  # Penalty per idle step (increased)
            
            # Cycle state tracking
            'cycle_progress_bonus': 0.05,  # Small bonus for making progress in cycle
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
            2 +  # seed inventory counts (normalized)
            # Phase 2 additions:
            1 +  # day_progress (normalized)
            1 +  # distance_to_trader (normalized)
            1 +  # distance_to_harvestable (normalized)
            1 +  # crops_per_day (efficiency metric)
            1    # money_per_step (efficiency metric)
        )  # Total: 25
        
        # Grid observation: (W, W, C) where C = 7 channels
        # Channels: farmable, tilled, watered, planted, plant_type/growth, tree_present, tree_health
        grid_channels = 7
        
        # Action history: flattened array of past actions (5 branches per action)
        action_history_flat_size = action_history_size * 5  # 5 action branches
        
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
            ),
            "action_history": spaces.Box(
                low=0.0,
                high=1.0,
                shape=(action_history_flat_size,),
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
        
        # Phase 2: Action history buffer
        self.action_history = deque(maxlen=action_history_size)
        # Initialize with zeros (no-op actions)
        for _ in range(action_history_size):
            self.action_history.append(np.zeros(5, dtype=np.float32))
        
        # Phase 2: Efficiency metrics tracking
        self.crops_harvested_this_episode = 0
        self.money_earned_this_episode = 0
        
        # Phase 3: Farming cycle tracking
        # Track sequence: till → water → plant → harvest
        self.farming_cycle_state = {
            'tilled': False,
            'watered': False,
            'planted': False,
            'started_at_step': None,  # Track when cycle started
            'last_progress_step': None,  # Track last time cycle made progress
        }
        self.farming_cycles_completed = 0
        self.incomplete_cycles = 0  # Track abandoned cycles
        
        # Phase 3: Crop diversity tracking
        self.crops_harvested_by_type = {'corn': 0, 'tomato': 0}
        
        # Phase 3: Idle tracking
        self.steps_since_productive_action = 0
        
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
        
        # Reset action history with zeros
        self.action_history.clear()
        for _ in range(self.action_history_size):
            self.action_history.append(np.zeros(5, dtype=np.float32))
        
        # Reset efficiency metrics
        self.crops_harvested_this_episode = 0
        self.money_earned_this_episode = 0
        
        # Reset Phase 3 tracking
        self.farming_cycle_state = {
            'tilled': False,
            'watered': False,
            'planted': False,
            'started_at_step': None,
            'last_progress_step': None,
        }
        self.farming_cycles_completed = 0
        self.incomplete_cycles = 0
        self.crops_harvested_by_type = {'corn': 0, 'tomato': 0}
        self.steps_since_productive_action = 0
        self._diversity_bonus_applied = False  # Track if diversity bonus was applied
        
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
            self.level.player.env_events = self.events  # For invalid action tracking
        
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
        
        # Record action in history (normalized to [0, 1])
        # Normalization: move/5, tool/3, seed/3, interact/2, menu/5
        action_normalized = np.array([
            move_action / 4.0,
            tool_action / 2.0,
            seed_action / 2.0,
            interact_action / 1.0,
            menu_action / 4.0
        ], dtype=np.float32)
        self.action_history.append(action_normalized)
        
        # Update efficiency metrics based on events
        for event in self.events:
            if event == 'harvest':
                self.crops_harvested_this_episode += 1
        
        # Track money earned (positive money delta)
        money_delta = self.level.player.money - self.prev_money
        if money_delta > 0:
            self.money_earned_this_episode += money_delta
        
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
        
        # Phase 2: Additional observation features
        # Day progress (normalized)
        day_progress = min(self.day_count / max(self.max_days, 1), 1.0)
        
        # Distance to trader (normalized)
        trader_distance_norm = 1.0  # Default to max distance if no trader found
        for sprite in self.level.interaction_sprites.sprites():
            if hasattr(sprite, 'name') and sprite.name == 'Trader':
                trader_pos = pygame.math.Vector2(sprite.rect.centerx, sprite.rect.centery)
                player_pos = pygame.math.Vector2(player.pos.x, player.pos.y)
                distance = (trader_pos - player_pos).length()
                # Normalize by max map distance (assume ~2000 pixels max)
                trader_distance_norm = min(distance / 2000.0, 1.0)
                break
        
        # Distance to nearest harvestable crop (normalized)
        harvestable_distance_norm = 1.0  # Default to max distance if no harvestable found
        min_distance = float('inf')
        for plant in self.level.soil_layer.plant_sprites.sprites():
            if hasattr(plant, 'harvestable') and plant.harvestable:
                plant_pos = pygame.math.Vector2(plant.rect.centerx, plant.rect.centery)
                player_pos = pygame.math.Vector2(player.pos.x, player.pos.y)
                distance = (plant_pos - player_pos).length()
                if distance < min_distance:
                    min_distance = distance
        if min_distance < float('inf'):
            harvestable_distance_norm = min(min_distance / 2000.0, 1.0)
        
        # Phase 2: Efficiency metrics
        # Crops per day (normalized, assume max ~20 crops per day is excellent)
        crops_per_day = self.crops_harvested_this_episode / max(self.day_count, 1)
        crops_per_day_norm = min(crops_per_day / 20.0, 1.0)
        
        # Money per step (normalized, assume max ~1 money per step is excellent)
        money_per_step = self.money_earned_this_episode / max(self.step_count, 1)
        money_per_step_norm = min(money_per_step / 1.0, 1.0)
        
        # Build player state vector
        player_state = np.concatenate([
            [player_tile_x, player_tile_y],
            facing_onehot,
            tool_onehot,
            seed_onehot,
            [raining, shop_active, money_norm],
            item_inv,
            seed_inv,
            # Phase 2 additions:
            [day_progress, trader_distance_norm, harvestable_distance_norm,
             crops_per_day_norm, money_per_step_norm]
        ], dtype=np.float32)
        
        # Grid observation (local window around player)
        grid_obs = self._get_grid_observation(player_tile_x, player_tile_y)
        
        # Flatten action history for observation
        action_history_flat = np.concatenate(list(self.action_history), dtype=np.float32)
        
        return {
            "player": player_state,
            "grid": grid_obs,
            "action_history": action_history_flat
        }
    
    def _get_grid_observation(self, center_x: int, center_y: int) -> np.ndarray:
        """Extract local grid window around player"""
        window_size = self.grid_window_size
        half_window = window_size // 2
        
        # Initialize grid tensor: (W, W, 7)
        # Channels: farmable, tilled, watered, planted, plant_type_norm, tree_present, tree_health
        grid = np.zeros((window_size, window_size, 7), dtype=np.float32)
        
        # Create plant lookup dict for efficiency
        plant_lookup = {}
        for plant in self.level.soil_layer.plant_sprites.sprites():
            tx = int(plant.rect.centerx) // TILE_SIZE
            ty = int(plant.rect.centery) // TILE_SIZE
            plant_lookup[(tx, ty)] = plant
        
        # Create tree lookup dict for tree channels
        tree_lookup = {}
        for tree in self.level.tree_sprites.sprites():
            tx = int(tree.rect.centerx) // TILE_SIZE
            ty = int(tree.rect.centery) // TILE_SIZE
            tree_lookup[(tx, ty)] = tree
        
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
                    
                    # Channel 5: Tree present (binary)
                    # Channel 6: Tree health (normalized 0-1)
                    if (tx, ty) in tree_lookup:
                        tree = tree_lookup[(tx, ty)]
                        grid[gy, gx, 5] = 1.0  # Tree present
                        # Normalize health (max health is 5)
                        if hasattr(tree, 'health') and hasattr(tree, 'alive'):
                            if tree.alive:
                                grid[gy, gx, 6] = min(tree.health / 5.0, 1.0)
                            else:
                                grid[gy, gx, 6] = 0.0  # Dead tree (stump)
                # Out of bounds: all zeros (already initialized)
        
        return grid
    
    def _compute_reward(self) -> float:
        """Compute reward based on events and state changes with comprehensive cycle tracking"""
        reward = 0.0
        
        # Step penalty
        reward += self.reward_config['step_penalty']
        
        # Money delta (profit)
        money_delta = self.level.player.money - self.prev_money
        
        # Track if this step had a productive action
        productive_action = False
        cycle_progress_made = False
        
        # Check for incomplete cycle abandonment
        if (self.farming_cycle_state['started_at_step'] is not None and 
            self.farming_cycle_state['last_progress_step'] is not None):
            steps_since_progress = self.step_count - self.farming_cycle_state['last_progress_step']
            if steps_since_progress > self.reward_config['cycle_abandonment_threshold']:
                # Cycle abandoned - apply penalty
                reward += self.reward_config['incomplete_cycle_penalty']
                self.incomplete_cycles += 1
                # Reset cycle state
                self.farming_cycle_state = {
                    'tilled': False,
                    'watered': False,
                    'planted': False,
                    'started_at_step': None,
                    'last_progress_step': None,
                }
        
        # Event-based rewards
        for event in self.events:
            if event == 'till_success':
                reward += self.reward_config['till_success']
                productive_action = True
                cycle_progress_made = True
                
                # Start or continue cycle
                if self.farming_cycle_state['started_at_step'] is None:
                    self.farming_cycle_state['started_at_step'] = self.step_count
                self.farming_cycle_state['tilled'] = True
                self.farming_cycle_state['last_progress_step'] = self.step_count
                
                # Progress bonus
                reward += self.reward_config['cycle_progress_bonus']
                
            elif event == 'water_success':
                reward += self.reward_config['water_success']
                productive_action = True
                cycle_progress_made = True
                
                # Continue cycle
                if self.farming_cycle_state['started_at_step'] is None:
                    self.farming_cycle_state['started_at_step'] = self.step_count
                self.farming_cycle_state['watered'] = True
                self.farming_cycle_state['last_progress_step'] = self.step_count
                
                # Progress bonus
                reward += self.reward_config['cycle_progress_bonus']
                
            elif event == 'plant_success':
                reward += self.reward_config['plant_success']
                productive_action = True
                cycle_progress_made = True
                
                # Continue cycle
                if self.farming_cycle_state['started_at_step'] is None:
                    self.farming_cycle_state['started_at_step'] = self.step_count
                self.farming_cycle_state['planted'] = True
                self.farming_cycle_state['last_progress_step'] = self.step_count
                
                # Progress bonus
                reward += self.reward_config['cycle_progress_bonus']
                
            elif event == 'harvest':
                reward += self.reward_config['harvest_bonus']
                productive_action = True
                cycle_progress_made = True
                
                # Check for complete farming cycle
                cycle_complete = (self.farming_cycle_state['tilled'] and 
                                 self.farming_cycle_state['watered'] and 
                                 self.farming_cycle_state['planted'])
                
                if cycle_complete:
                    # MAJOR REWARD: Complete cycle
                    reward += self.reward_config['cycle_completion_bonus']
                    self.farming_cycles_completed += 1
                    
                    # Efficiency bonus (faster cycles are better)
                    if self.farming_cycle_state['started_at_step'] is not None:
                        cycle_duration = self.step_count - self.farming_cycle_state['started_at_step']
                        if cycle_duration < 200:  # Fast cycle
                            reward += self.reward_config['cycle_efficiency_bonus']
                    
                    # Profit-based bonus (if crop was sold)
                    # This will be added when sell_item event occurs
                    
                # Reset cycle state
                self.farming_cycle_state = {
                    'tilled': False,
                    'watered': False,
                    'planted': False,
                    'started_at_step': None,
                    'last_progress_step': None,
                }
                
            elif event == 'sell_item':
                reward += self.reward_config['sell_bonus']
                productive_action = True
                
                # Profit-based bonus
                if money_delta > 0:
                    # Calculate profit (sale price - purchase price if applicable)
                    # For crops: corn=$10, tomato=$20
                    # For resources: wood=$4, apple=$2
                    profit = money_delta
                    reward += self.reward_config['sell_profit_bonus_scale'] * profit
                    
                    # If this was part of a cycle, add cycle profit bonus
                    if self.farming_cycles_completed > 0:
                        reward += self.reward_config['cycle_profit_bonus_scale'] * profit
                
            elif event == 'buy_seed':
                reward += self.reward_config['buy_seed_bonus']
                productive_action = True
                
                # Bonus for buying seeds when inventory is low
                total_seeds = sum(self.level.player.seed_inventory.values())
                if total_seeds < 3:
                    reward += self.reward_config['low_seed_purchase_bonus']
                
                # Bonus for buying tomato seeds (higher value)
                # This is tracked in menu.py, but we can infer from seed inventory
                
            elif event == 'invalid_action':
                reward += self.reward_config['invalid_action_penalty']
                
            elif event == 'apple_collect':
                reward += self.reward_config['apple_collect_bonus']
                productive_action = True
                
            elif event == 'wood_collect':
                reward += self.reward_config['wood_collect_bonus']
                productive_action = True
                
            elif event == 'day_reset':
                reward += self.reward_config['day_complete_bonus']
                # Reset cycle state on day reset
                self.farming_cycle_state = {
                    'tilled': False,
                    'watered': False,
                    'planted': False,
                    'started_at_step': None,
                    'last_progress_step': None,
                }
                
            # Track crop type for diversity
            elif event == 'harvest_corn':
                self.crops_harvested_by_type['corn'] += 1
            elif event == 'harvest_tomato':
                self.crops_harvested_by_type['tomato'] += 1
                reward += self.reward_config['tomato_preference_bonus']
        
        # Money-based rewards (after events to capture profit)
        reward += self.reward_config['money_scale'] * money_delta
        
        # Spending penalty
        if money_delta < 0:
            reward += self.reward_config['spend_penalty_scale'] * abs(money_delta)
        
        # Crop diversity bonus (applied once per episode when both types harvested)
        if (self.crops_harvested_by_type['corn'] > 0 and 
            self.crops_harvested_by_type['tomato'] > 0):
            # Apply diversity bonus (only once, tracked per episode)
            if not hasattr(self, '_diversity_bonus_applied'):
                reward += self.reward_config['diversity_bonus']
                self._diversity_bonus_applied = True
        
        # Action spam detection (no events but actions were taken)
        if not productive_action and len(self.events) == 0:
            # Check if agent tried to take actions (would be in action history)
            # This is a proxy for action spam during cooldowns
            # We'll penalize if no productive action and no events
            pass  # Handled by idle penalty below
        
        # Idle penalty
        if productive_action:
            self.steps_since_productive_action = 0
        else:
            self.steps_since_productive_action += 1
        
        idle_threshold = self.reward_config['idle_penalty_threshold']
        if self.steps_since_productive_action > idle_threshold:
            excess_idle = self.steps_since_productive_action - idle_threshold
            reward += self.reward_config['idle_penalty_scale'] * excess_idle
        
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
