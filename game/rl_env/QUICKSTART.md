/code# Quick Start Guide

## Step 1: Apply Integration Patches

**IMPORTANT**: Before using the RL environment, you must apply the integration patches to your game code.

See `INTEGRATION_PATCHES.md` for detailed instructions. The patches modify:
1. `code/player.py` - Add agent controls support
2. `code/level.py` - Add agent controls and event collection
3. `code/soil.py` - Add event emission for rewards
4. `code/menu.py` - Add agent controls for shop menu

## Step 2: Install Dependencies

```bash
pip install gymnasium stable-baselines3[extra] numpy pygame pytmx
pip install tensorboard  # Optional, for training logs
```

## Step 3: Test Environment (Optional)

Create a simple test script to verify the environment works:

```python
from sproutland_env import SproutLandEnv

env = SproutLandEnv(render_mode="human", max_steps=1000)
obs, info = env.reset()
print("Observation space:", env.observation_space)
print("Action space:", env.action_space)

# Run a few random steps
for i in range(10):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step {i}: Reward={reward:.3f}, Money=${info['money']}")
    if terminated or truncated:
        break

env.close()
```

## Step 4: Train a Model

Basic training (short test):
```bash
python train_ppo.py --total-timesteps 100000 --n-envs 4
```

Full training run:
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

## Step 5: Evaluate Trained Model

Evaluate model:
```bash
python evaluate.py ./models/ppo_sproutland_final.zip --n-episodes 10 --render
```

Run single interactive episode:
```bash
python evaluate.py ./models/ppo_sproutland_final.zip --single --render
```

## Troubleshooting

### Import Errors
- Make sure integration patches are applied
- Check that paths are correct (rl_env/ and code/ directories)
- Try: `cd rl_env && python -c "from sproutland_env import SproutLandEnv"`

### Environment Creation Errors
- Verify pygame initializes correctly
- Check that all game assets (graphics, audio, data) are in correct paths
- Test original game runs first: `python code/main.py`

### Training Errors
- Start with short training runs to test
- Check that events are being emitted (see integration patches)
- Verify agent controls are working (check that player moves with agent actions)

### Performance Issues
- Use `render_mode="none"` for training (default)
- Increase `n_envs` for faster training (if CPU allows)
- Reduce `grid_window_size` if memory is limited

## Next Steps

1. Apply integration patches
2. Run a short training test (10k steps)
3. Evaluate the model
4. Adjust hyperparameters and reward function
5. Scale up for longer training runs
6. Monitor tensorboard logs: `tensorboard --logdir ./tensorboard`

## File Overview

- `sproutland_env.py`: Main Gymnasium environment
- `wrappers.py`: Optional wrappers (normalization, action masking, logging)
- `train_ppo.py`: PPO training script with Stable-Baselines3
- `evaluate.py`: Model evaluation script
- `README.md`: Full documentation
- `INTEGRATION_PATCHES.md`: Detailed integration instructions
