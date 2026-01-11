# SproutLand RL Environment

Reinforcement Learning environment for the SproutLand (Stardew Valley-style) farming game using Gymnasium and Stable-Baselines3.

## Installation

### Requirements

```bash
pip install gymnasium stable-baselines3[extra] numpy pygame pytmx
```

Optional for tensorboard logging:
```bash
pip install tensorboard
```

## Project Structure

```
rl_env/
├── sproutland_env.py    # Main Gymnasium environment class
├── wrappers.py          # Optional wrappers (normalization, action masking, logging)
├── train_ppo.py         # PPO training script
├── evaluate.py          # Model evaluation script
└── README.md            # This file
```

## Quick Start

### 1. Apply Integration Patches

Before using the RL environment, you must apply the integration patches to your game code:

1. **Modify `code/player.py`**: Add agent control support (see integration instructions below)
2. **Modify `code/level.py`**: Add agent control interface and event collection
3. **Modify `code/menu.py`**: Add agent control support for shop menu

See the integration patches section below for detailed instructions.

### 2. Train a Model

```bash
cd rl_env
python train_ppo.py --total-timesteps 1000000 --n-envs 4
```

With custom parameters:
```bash
python train_ppo.py \
    --total-timesteps 2000000 \
    --n-envs 8 \
    --learning-rate 3e-4 \
    --max-steps 10000 \
    --max-days 30 \
    --log-dir ./logs \
    --save-dir ./models \
    --tensorboard-log ./tensorboard
```

### 3. Evaluate a Trained Model

Run evaluation episodes:
```bash
python evaluate.py ./models/ppo_sproutland_final.zip --n-episodes 10 --render
```

Run a single interactive episode:
```bash
python evaluate.py ./models/ppo_sproutland_final.zip --single --render
```

## Environment Details

### Action Space

MultiDiscrete with 5 branches:
- **move**: [0-4] noop, up, down, left, right
- **tool_action**: [0-2] noop, switch_tool, use_tool
- **seed_action**: [0-2] noop, switch_seed, plant_seed
- **interact**: [0-1] noop, interact
- **menu_action**: [0-4] noop, up, down, select, exit

**Rules**:
- If `shop_active=False`: ignore `menu_action`, use other actions
- If `shop_active=True`: ignore movement/tool/seed actions, use `menu_action` only
- The `ActionMasking` wrapper automatically enforces these rules

### Observation Space

Dict with two components:

1. **"player"**: 1D float vector (20 elements)
   - Player tile coordinates (x, y)
   - Facing direction one-hot (4)
   - Selected tool one-hot (3: hoe, axe, water)
   - Selected seed one-hot (2: corn, tomato)
   - Raining (0/1)
   - Shop active (0/1)
   - Money (normalized)
   - Item inventory counts (wood, apple, corn, tomato) - normalized
   - Seed inventory counts (corn, tomato) - normalized

2. **"grid"**: Local tile window tensor (W×W×5) where W=9 by default
   - Channel 0: Farmable (binary)
   - Channel 1: Tilled (binary)
   - Channel 2: Watered (binary)
   - Channel 3: Planted (binary)
   - Channel 4: Plant type and growth stage (normalized: corn=0.5, tomato=1.0, scaled by growth)

### Reward Function

- **Step penalty**: -0.001 per step (encourage efficiency)
- **Money delta**: +0.01 × money_change (profit reward)
- **Spending penalty**: -0.005 × abs(money_loss) (optional)
- **Harvest bonus**: +0.25 per crop harvested
- **Action bonuses**: +0.01 for successful till/water/plant actions
- **Invalid action penalty**: -0.01 for invalid actions

### Episode Termination

- **Truncation**: 
  - Max steps reached (default: 10,000)
  - Max days reached (default: 30)
- **Termination** (optional):
  - Money target reached (if configured)

## Training Configuration

### Default Hyperparameters

- **Algorithm**: PPO (Proximal Policy Optimization)
- **Policy**: MultiInputPolicy (for Dict observation space)
- **Learning rate**: 3e-4
- **Batch size**: 256
- **N steps**: 2048
- **N epochs**: 10
- **Gamma**: 0.99
- **GAE lambda**: 0.95
- **Entropy coefficient**: 0.01
- **Clip range**: 0.2

### Customizing Training

Edit `train_ppo.py` or use command-line arguments to customize:
- Learning rate, batch size, etc.
- Environment parameters (max_steps, max_days, grid_window_size)
- Reward configuration
- Number of parallel environments

## Integration Instructions

### Step 1: Modify `code/player.py`

Add the following code after line 64 (after `self.toggle_shop = toggle_shop`):

```python
# RL agent controls
self.use_agent_controls = False
self.agent_controls = None  # Will be set by Level
```

Modify the `input()` method (starting at line 110) to check for agent controls:

```python
def input(self):
    # ADAPT THIS BLOCK: Use agent controls if enabled
    if hasattr(self, 'use_agent_controls') and self.use_agent_controls and self.agent_controls:
        self._process_agent_input()
    else:
        self._process_keyboard_input()

def _process_keyboard_input(self):
    """Original keyboard input processing"""
    keys = pygame.key.get_pressed()
    # ... (rest of original input() code)
    
def _process_agent_input(self):
    """Process agent controls"""
    controls = self.agent_controls
    # ... (see integration patch file for full implementation)
```

### Step 2: Modify `code/level.py`

Add after line 39 (after `self.shop_active = False`):

```python
# RL agent controls
self.use_agent_controls = False
self.agent_controls = None  # AgentControls dataclass
self.env_events = []  # Event list for reward computation
self.day_count = 0  # Track days for episode termination
```

Modify `reset()` method to increment day_count:

```python
def reset(self):
    # ... existing code ...
    self.day_count += 1
    # ... rest of code ...
```

Modify `player_add()` to emit events:

```python
def player_add(self, item):
    self.player.item_inventory[item] += 1
    self.success.play()
    # ADAPT THIS BLOCK: Emit harvest event
    if hasattr(self, 'env_events'):
        if item in ['corn', 'tomato']:
            self.env_events.append('harvest')
```

### Step 3: Modify `code/menu.py`

Add agent control support to `input()` method. See integration patch files for full details.

## Files Overview

### `sproutland_env.py`

Main environment class implementing Gymnasium Env interface:
- `reset()`: Reset environment to initial state
- `step(action)`: Execute action and return observation, reward, done, info
- `render()`: Render environment (human or headless)
- Observation extraction from game state
- Reward computation from events and state changes

### `wrappers.py`

Optional wrappers:
- `NormalizeObservation`: Normalize observations to [-1, 1]
- `ActionMasking`: Mask invalid actions based on game state
- `ActionAdapter`: Adapt actions (can be extended)
- `LoggingWrapper`: Log training statistics

### `train_ppo.py`

Training script using Stable-Baselines3 PPO:
- Vectorized environments (DummyVecEnv or SubprocVecEnv)
- Evaluation callbacks
- Checkpoint saving
- Tensorboard logging
- Command-line interface

### `evaluate.py`

Evaluation script:
- Load trained models
- Run evaluation episodes
- Collect statistics
- Optionally render episodes
- Single interactive episode mode

## Troubleshooting

### Import Errors

If you get import errors, ensure:
1. Integration patches are applied
2. Path structure is correct (rl_env/ and code/ directories)
3. All dependencies are installed

### Rendering Issues

- Set `render_mode="none"` for headless training
- Use `render_mode="human"` only for evaluation/visualization
- Rendering significantly slows down training

### Performance

- Use multiple parallel environments (`--n-envs 4` or more)
- Use `SubprocVecEnv` for faster training (default in train_ppo.py)
- Disable rendering during training
- Use smaller `grid_window_size` if memory is limited

### Training Issues

- Start with default hyperparameters
- Monitor tensorboard logs for training progress
- Adjust reward scales if agent behavior is poor
- Check that events are being emitted correctly (integration patches)

## Next Steps

1. Apply integration patches to game code
2. Run a short training test: `python train_ppo.py --total-timesteps 10000`
3. Evaluate the trained model: `python evaluate.py ./models/ppo_sproutland_final.zip --single`
4. Adjust hyperparameters and reward function as needed
5. Scale up training for longer runs

## Notes

- The environment uses fixed delta-time (`1/60s`) during training for determinism
- Agent controls completely bypass keyboard input when enabled
- Events are collected each step for reward computation
- Grid observation uses a local window around the player (configurable size)
- Day counting is tracked for episode termination
