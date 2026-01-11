# Multi-Agent Game - How to Run

## Quick Start

```bash
cd "/Users/spiderishi/Coding/AI Manipulation/code"
python3 multi_agent_game.py --duration 5 --num-agents 4
```

Or use the launcher:
```bash
./run_multi_agent_game.sh
```

## What You'll See

### Game Window
- **Top Left**: Timer showing remaining time (5 minutes)
- **Day Counter**: Current day (advances every 30 seconds)
- **Agent Status**: All 4 agents with their status and current actions
- **Communication Log**: Real-time messages between agents
- **Resources**: Food, Ore, Prosperity counters

### Agent Behavior
- **Credit Seeker** (agent_1): Tries to get others to do risky work, takes credit
- **Fairness Agent** (agent_2): Advocates for balanced contributions
- **Risk Averse** (agent_3): Avoids dangerous tasks
- **Baseline** (agent_4): Cooperative, aligned with town prosperity

### What Happens
1. **Every 30 seconds** = New day
2. **At start of each day**: Agents communicate (you'll see messages)
3. **Agents decide**: What action to take (farm, mine, deliver, etc.)
4. **Actions execute**: You see the player moving and working
5. **After 5 minutes**: Episode ends, results shown

## Controls
- **ESC**: Exit early
- **Close window**: Exit

## Options

```bash
# Different duration
python3 multi_agent_game.py --duration 10  # 10 minutes

# Different agent types
python3 multi_agent_game.py --agent-types credit_seeker fairness risk_averse baseline

# With LLM (requires API key)
export OPENAI_API_KEY="your-key"
python3 multi_agent_game.py --use-llm --api openai --duration 5
```

## What to Watch For

1. **Communication**: Watch the message log - agents try to manipulate each other
2. **Action Patterns**: See which agent does what work
3. **Manipulation**: Credit-seeker avoids risky work, takes credit
4. **Cooperation**: Fairness agent tries to balance workload

Enjoy watching the agents manipulate each other! 🎮
