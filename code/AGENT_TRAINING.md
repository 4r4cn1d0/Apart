# Agent Training System

## Overview

The agents can now learn to play the game through:
1. **Vision-based decision making** - Agents see the game screen
2. **Experience learning** - Agents learn from past episodes
3. **Pattern recognition** - Successful strategies are identified
4. **Knowledge base** - Game mechanics are learned over time

## How It Works

### 1. Vision-Based Agents (Game-Aware)

When using LLM agents, they can see the game screen and make informed decisions:

```bash
export OPENAI_API_KEY="your-key"
python3 multi_agent_game.py --duration 5 --use-llm --api openai
```

The agent will:
- See the current game state visually
- Understand where objects are (trees, soil, trader)
- Make context-aware decisions
- Learn from outcomes

### 2. Training Episodes

Run training episodes to build a knowledge base:

```bash
python3 train_agents.py --episodes 10
```

This will:
- Run multiple simulation episodes
- Record successful patterns
- Build a knowledge base of strategies
- Save learned patterns to `agent_knowledge.json`

### 3. Using Trained Knowledge

Trained agents automatically use learned patterns:
- Successful action sequences
- Communication strategies that work
- Risk assessment patterns
- Resource management strategies

## Training Process

1. **Run Episodes**: Agents play the game multiple times
2. **Extract Patterns**: Successful strategies are identified
3. **Build Knowledge**: Patterns stored in knowledge base
4. **Apply Learning**: Future agents use learned knowledge

## Example Training Session

```bash
# Step 1: Train agents
python3 train_agents.py --episodes 20

# Step 2: Run game with trained agents
python3 multi_agent_game.py --duration 5 --use-llm
```

## What Agents Learn

- **Game Mechanics**: How tools work, where objects are
- **Action Sequences**: What actions lead to success
- **Communication**: Effective persuasive strategies
- **Risk Assessment**: When to take risks vs avoid them
- **Resource Management**: How to manage inventory

## Advanced: Custom Training

You can create custom training scenarios:

```python
from train_agents import AgentTrainer

trainer = AgentTrainer()
# Run custom scenarios
# Extract specific patterns
# Build domain knowledge
```

## Next Steps

1. **More Training Data**: Run more episodes for better learning
2. **Fine-tuning**: Adjust agent behavior based on outcomes
3. **Specialized Training**: Train agents for specific scenarios
4. **Transfer Learning**: Apply knowledge across different conditions

The more episodes you run, the smarter the agents become! 🧠
