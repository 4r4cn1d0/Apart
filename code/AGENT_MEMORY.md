# Agent Memory System - Persistent Learning

## ✅ Yes, Agents Now Remember Between Sessions!

Agents now have **persistent memory** that saves between game runs. They remember what they learned and use it in future sessions.

## How It Works

### 1. **During Gameplay** 
- Agents perform actions (farm, mine, deliver, etc.)
- Each action and its outcome is recorded
- Successful patterns are identified and saved
- Tool usage and locations are tracked

### 2. **Memory Storage**
- All experiences saved to `agent_memory.json` 
- Includes:
  - Action sequences that worked well
  - Tool usage patterns by location
  - Success/failure outcomes
  - Agent-specific learning patterns

### 3. **When Game Starts**
- Memory is automatically loaded from `agent_memory.json`
- Agents receive their learned patterns from previous sessions
- They use this knowledge to make better decisions

### 4. **When Game Ends**
- Memory is automatically saved
- New experiences are added to the knowledge base
- Agents get smarter over time!

## What Agents Remember

### Successful Action Patterns
- Which actions led to good outcomes
- Action sequences that worked well
- Patterns per agent type (credit_seeker, fairness, etc.)

### Tool Usage
- Where each tool works best
- Successful vs failed tool usage by location
- Optimal tool selection strategies

### Agent-Specific Learning
- Credit Seekers learn: "Deliver actions give me credit"
- Risk Averse learn: "Mining is dangerous, avoid it"
- Fairness learn: "Balanced actions work well"
- Baseline learn: "Farming produces prosperity"

## Memory File Location

**File**: `code/agent_memory.json`

Contains:
```json
{
  "agent_experiences": {
    "agent_1": [...],
    "agent_2": [...]
  },
  "successful_patterns": {
    "credit_seeker": [...],
    "baseline": [...]
  },
  "tool_strategies": {...},
  "episode_count": 5,
  "total_actions": 1234
}
```

## Usage

**Nothing extra needed!** Memory works automatically:

```bash
# First run - agents learn
python3 multi_agent_game.py --num-agents 4

# Second run - agents use what they learned!
python3 multi_agent_game.py --num-agents 4

# Agents now remember:
# - What actions worked well
# - Which tools to use where
# - Their successful strategies
```

## Memory Stats

When you start the game, you'll see:
```
📚 Agent Memory: 3 episodes, 456 actions learned
✅ Loaded existing knowledge: 45 patterns
  Created agent_1 (credit_seeker) with 12 learned patterns
```

## Benefits

✅ **Continuous Learning**: Agents improve over time  
✅ **No Relearning**: They remember what works  
✅ **Agent-Specific**: Each agent type learns differently  
✅ **Automatic**: No manual setup required  
✅ **Persistent**: Survives game restarts  

## Resetting Memory

To start fresh (erase memory):
```bash
rm code/agent_memory.json
```

Agents will start learning from scratch again.

## Memory Limits

- Last 100 experiences per agent (to prevent file bloat)
- Last 50 successful patterns per agent type
- Memory file auto-manages size

---

**Agents now learn and remember across sessions!** 🧠💾
