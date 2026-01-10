# Agent Training Guide

## 🚀 Training Started!

The agent training system is now running with comprehensive training parameters.

## Training Configuration

**Current Run:**
- **Episodes:** 30 episodes
- **Duration:** 3 minutes per day
- **Days per Episode:** 3 days
- **Total Training Time:** ~4.5 hours (30 episodes × 3 days × 3 minutes = 270 minutes)

**Why These Parameters:**
- 30 episodes provides substantial learning (good balance)
- 3 minutes per day is faster than 5 minutes but still allows agents to learn
- 3 days per episode is sufficient to see patterns without being too long
- Total time is reasonable (~4.5 hours) while still being comprehensive

## What's Being Trained

### 1. **Critic-Based Reward System** (Triforce-style)
- Agents receive rewards from multiple critics:
  - **ProsperityCritic**: Rewards town prosperity gains
  - **CreditCritic**: Rewards credit-seeking behavior
  - **SafetyCritic**: Penalizes risky actions
  - **EfficiencyCritic**: Rewards resource gathering
  - **FairnessCritic**: Rewards balanced contributions

### 2. **Experience Memory**
- All actions and outcomes are recorded
- Successful patterns are identified and stored
- Agents learn from past experiences

### 3. **Manipulation Patterns**
- Risk shifting (pushing risky tasks to others)
- Credit capture (claiming credit-worthy tasks)
- Persuasion attempts (influencing others)
- Deceptive messaging (if it emerges)

## Training Output

### Files Created:
1. **`training_output/training_metrics_YYYYMMDD_HHMMSS.json`**
   - Complete training metrics
   - Episode-by-episode performance
   - Best episode records
   - Improvement tracking

2. **`training_output/checkpoint_ep10.json`**, `checkpoint_ep20.json`, etc.
   - Periodic checkpoints every 10 episodes
   - Allows resuming if interrupted

3. **`agent_memory.json`**
   - Persistent agent memory
   - Updated after each episode
   - Contains learned patterns and experiences

## Monitor Training

### Check Progress:
```bash
# Watch training log (if running in foreground)
tail -f training.log

# Check memory stats
python3 -c "from multi_agent.agent_memory import get_agent_memory; m = get_agent_memory(); print(m.get_stats())"

# Check checkpoint files
ls -lt training_output/checkpoint_*.json | head -5
```

### Expected Progress Indicators:
- **Episode 5**: Agents start showing basic understanding
- **Episode 10**: First checkpoint saved
- **Episode 15**: Patterns emerging
- **Episode 20**: Second checkpoint saved
- **Episode 30**: Final metrics saved

## Stop/Resume Training

### Stop Training:
Press `Ctrl+C` - training will save current progress before stopping.

### Resume Training:
Training automatically saves checkpoints. To resume:
```python
# Load from checkpoint
import json
with open('training_output/checkpoint_ep20.json', 'r') as f:
    checkpoint = json.load(f)
# Continue from episode 21
```

## Adjust Training Parameters

### For Faster Training (Less Comprehensive):
```bash
python3 train_game_agents.py --episodes 20 --duration 2 --days 2
# ~1.3 hours total
```

### For More Comprehensive Training:
```bash
python3 train_game_agents.py --episodes 50 --duration 5 --days 5
# ~10+ hours total (run overnight)
```

### For Quick Test Run:
```bash
python3 train_game_agents.py --episodes 5 --duration 1 --days 1
# ~5 minutes total
```

## After Training Completes

### 1. Check Results
```bash
# View final metrics
cat training_output/training_metrics_*.json | python3 -m json.tool | head -50

# Check memory
python3 -c "from multi_agent.agent_memory import get_agent_memory; m = get_agent_memory(); import json; print(json.dumps(m.get_stats(), indent=2))"
```

### 2. Run Game with Trained Agents
```bash
python3 multi_agent_game.py --num-agents 4
```

Agents will automatically use learned patterns from training!

### 3. Analyze Training Data
```python
import json

# Load metrics
with open('training_output/training_metrics_*.json', 'r') as f:
    metrics = json.load(f)

# Analyze
summary = metrics['summary']
print(f"Best Prosperity: {summary['best_prosperity']}")
print(f"Average Prosperity: {summary['avg_prosperity']}")
print(f"Improvement: {summary['improvement']}")
```

## Expected Outcomes

After 30 episodes, agents should:

✅ **Understand Game Mechanics**
- Know how to use tools (hoe, axe, water)
- Understand where objects are (trees, soil, trader)
- Know action outcomes (harvesting, mining, delivering)

✅ **Strategic Decision Making**
- Credit seekers prioritize delivering
- Risk-averse agents avoid mining
- Fairness agents advocate for balance
- Baseline agents cooperate

✅ **Learned Patterns**
- Successful action sequences
- When to switch tasks
- How to avoid injuries
- How to maximize rewards

✅ **Manipulation Emergence**
- Risk shifting (if incentives misaligned)
- Credit capture (if credit seekers present)
- Persuasion attempts (if communication enabled)

## Training Metrics Explained

- **Prosperity**: Town's overall prosperity (higher is better)
- **Total Reward**: Sum of all critic rewards (measures overall performance)
- **Credit Earned**: Personal credit points (for credit-seeking agents)
- **Actions Taken**: Number of actions per episode
- **Injuries**: Whether agent got injured (lower is better)

## Troubleshooting

### Training Takes Too Long
- Reduce episodes: `--episodes 20`
- Reduce duration: `--duration 2`
- Reduce days: `--days 2`

### Training Uses Too Much Memory
- Episodes create memory - this is normal
- Memory is saved periodically
- Can clear old checkpoints if needed

### Agents Not Learning
- Check that episodes are completing
- Verify memory is being saved
- Check for errors in training log
- Ensure episodes run long enough (at least 2-3 days)

## Next Steps After Training

1. **Evaluate Performance**: Compare trained vs untrained agents
2. **Analyze Patterns**: Study learned manipulation strategies
3. **Iterate**: Adjust training parameters based on results
4. **Expand**: Add more agent types or scenarios
5. **Research**: Use training data for manipulation research

---

**Training is currently running!** Check `training_output/` directory for progress updates.
