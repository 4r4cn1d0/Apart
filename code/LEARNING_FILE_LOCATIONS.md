# 📚 Where Actions and Learning Are Recorded

## Main Memory File: `agent_memory.json`

**Location:** `/Users/spiderishi/Coding/AI Manipulation/code/agent_memory.json`

This is the **persistent storage file** where all learning is saved. It contains:
- `agent_experiences`: All actions taken by each agent
- `successful_patterns`: Learned successful action patterns by agent type
- `tool_strategies`: Tool usage patterns
- `episode_count`: Total number of training episodes
- `total_actions`: Total number of actions recorded
- `last_updated`: Timestamp of last save

## Code Files That Handle Learning

### 1. Memory System: `multi_agent/agent_memory.py`

**Key Functions:**
- `record_experience(agent_id, agent_type, action, outcome)` - Records each action
- `save_memory()` - Saves to `agent_memory.json`
- `get_learned_patterns(agent_type)` - Retrieves learned patterns
- `get_agent_experience(agent_id)` - Gets all experiences for an agent

**Lines 52-86:** Where experiences are recorded and patterns are learned

### 2. Action Recording: `multi_agent_game.py`

**Key Function:**
- `_record_action_experience(agent, action, action_source)` - **Lines 789-905**

This function:
1. Tracks player state before/after actions
2. Calculates outcomes (success, money gained, inventory changes)
3. Uses critics to evaluate rewards (triforce-style)
4. Calls `self.memory.record_experience()` to save to memory

**Called from:**
- Line 369: When LLM agents take actions
- Line 390: When heuristic agents take actions
- Records every action in training/headless mode

### 3. Training Loop: `train_game_agents.py`

**Key Function:**
- `train_episode(episode_num)` - **Lines 126-243**

This function:
1. Runs a game episode
2. Wraps `_record_action_experience` to track rewards
3. Saves memory after each episode
4. Records metrics

## How Learning Works

1. **Agent Takes Action** → `multi_agent_game.py` processes it
2. **State Change Measured** → Money, inventory, prosperity tracked
3. **Outcome Calculated** → Success/failure determined
4. **Reward Calculated** → Critics evaluate the action
5. **Experience Recorded** → Saved to `agent_memory.json`
6. **Patterns Learned** → Successful actions become learned patterns
7. **Memory Loaded** → Next session uses learned patterns

## Viewing Learning in Real-Time

```bash
# Watch the memory file grow
watch -n 2 'python3 -c "from multi_agent.agent_memory import get_agent_memory; print(get_agent_memory().get_stats())"'

# View the memory file
cat agent_memory.json | python3 -m json.tool | less

# Check specific agent learning
python3 -c "
from multi_agent.agent_memory import get_agent_memory
mem = get_agent_memory()
for agent_id in ['agent_1', 'agent_2', 'agent_3', 'agent_4']:
    exp = mem.get_agent_experience(agent_id)
    if exp:
        print(f'{agent_id}: {len(exp)} experiences')
        print(f'  Recent actions: {[e.get(\"action\") for e in exp[-5:]]}')
"
```

## File Structure

```
code/
├── agent_memory.json          ← MAIN LEARNING FILE (grows as training progresses)
├── multi_agent/
│   └── agent_memory.py        ← Memory system code (loads/saves to JSON)
├── multi_agent_game.py        ← Records actions via _record_action_experience()
└── train_game_agents.py       ← Training loop (saves memory after episodes)
```

## What Gets Recorded

Each experience includes:
- `agent_id`: Which agent took the action
- `agent_type`: credit_seeker, fairness, risk_averse, baseline
- `action`: farm, mine, deliver, rest, move_*
- `outcome`: 
  - `success`: Did it work?
  - `prosperity_gain`: Town prosperity change
  - `credit`: Credit points earned
  - `money_gained`: Money earned
  - `inventory_change`: Items gained/lost
  - `rewards`: Critic-based rewards (triforce-style)
  - `total_reward`: Scalar reward value
- `timestamp`: When it happened

Successful patterns are extracted from experiences and stored separately for quick retrieval.
