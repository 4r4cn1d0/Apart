# Training Status

## Current Training Run

**Started:** Training is now running with the following configuration:
- **Episodes:** 50 episodes
- **Episode Duration:** 5 minutes each
- **Days per Episode:** 5 days
- **Total Training Time:** ~4+ hours (250+ minutes)

## What's Happening

1. **Episode Execution**: Each episode runs the full game for 5 days (5 minutes per day = 25 minutes per episode)
2. **Critic-Based Rewards**: Agents receive rewards from the triforce-style critic system
3. **Memory Accumulation**: All experiences are saved to `agent_memory.json`
4. **Pattern Learning**: Agents learn which actions lead to success
5. **Checkpoints**: Every 10 episodes, training state is saved

## Output Files

- `training_output/training_metrics_YYYYMMDD_HHMMSS.json` - Final training metrics
- `training_output/checkpoint_ep10.json`, `checkpoint_ep20.json`, etc. - Periodic checkpoints
- `agent_memory.json` - Persistent agent memory (updated after each episode)

## Monitor Training

To check progress, look for:
- Episode completion messages
- Progress updates every 5 episodes
- Checkpoint saves every 10 episodes

The training will show:
- Prosperity achieved per episode
- Total rewards
- Memory statistics
- Best episode performance

## After Training

Once training completes (or you can stop it early with Ctrl+C):
- Agents will have learned from all episodes
- Memory will be saved automatically
- You can run the game with trained agents: `python3 multi_agent_game.py --num-agents 4`

## Adjust Training

If you want to adjust training:

```bash
# Fewer episodes (faster)
python3 train_game_agents.py --episodes 20 --duration 3 --days 3

# More episodes (longer training)
python3 train_game_agents.py --episodes 100 --duration 5 --days 5

# Faster episodes for quick training
python3 train_game_agents.py --episodes 30 --duration 2 --days 2
```

## Expected Results

After 50 episodes, agents should:
- Understand game mechanics better
- Make more strategic decisions
- Show improved task switching
- Demonstrate learned manipulation patterns
- Have accumulated thousands of action experiences
