# How Agents Learn to Play the Game

## Three Ways Agents "Know" What to Do

### 1. **Vision-Based Learning** (Best - Agents See the Game)

When you use LLM agents with `--use-llm`, agents can **see the game screen** and learn naturally:

```bash
export OPENAI_API_KEY="your-key"
python3 multi_agent_game.py --duration 5 --use-llm --api openai
```

**How it works:**
- Every decision, agent sees a screenshot of the game
- LLM analyzes: "I see trees here, soil there, trader over there"
- Agent learns: "When I see brown soil, use hoe tool"
- Agent learns: "Trees are risky, avoid them"
- Agent learns: "Trader gives credit, go there"

**This is like human learning** - agents see and understand!

### 2. **Training Episodes** (Build Knowledge Base)

Run training episodes to extract successful patterns:

```bash
python3 train_agents.py --episodes 20
```

**What happens:**
- Runs 20 simulation episodes
- Records what actions lead to success
- Builds knowledge base of strategies
- Saves to `agent_knowledge.json`

**Agents learn:**
- "Credit-seekers who deliver early get more credit"
- "Avoiding mining prevents injuries"
- "Fairness messages increase cooperation"

### 3. **Experience Replay** (Learn from Outcomes)

Agents remember what worked:

- **Success**: "Delivering gave me credit → do more deliveries"
- **Failure**: "Mining caused injury → avoid mining"
- **Patterns**: "Farming is safe and productive"

## What Agents Learn

### Game Mechanics
- **Tools**: Hoe tills soil, Axe chops trees, Water helps crops
- **Locations**: Where trees are, where soil is, where trader is
- **Actions**: What each action does and its outcomes

### Strategies
- **Credit Seeker**: Deliver items → get credit → avoid risky work
- **Risk Averse**: Farm only → never mine → stay safe
- **Fairness**: Balance work → advocate for fairness
- **Baseline**: Maximize prosperity → work cooperatively

### Communication
- **What works**: Persuasive messages that get others to do work
- **What fails**: Messages that are ignored
- **Timing**: When to communicate vs when to act

## Training Process

### Step 1: Run Episodes
```bash
# Run 10 training episodes
python3 train_agents.py --episodes 10
```

### Step 2: Knowledge Extracted
- Successful action patterns identified
- Communication strategies recorded
- Risk patterns learned

### Step 3: Agents Use Knowledge
- Future agents reference learned patterns
- Better decision-making
- Improved manipulation strategies

## Vision vs Training

| Method | Speed | Quality | Cost |
|--------|-------|---------|------|
| **Vision** | Fast (real-time) | High (sees game) | API calls |
| **Training** | Slow (many episodes) | Medium (patterns) | Free |
| **Combined** | Medium | Highest | API calls |

## Best Practice

**Use both methods:**

1. **Train first** (build knowledge):
   ```bash
   python3 train_agents.py --episodes 20
   ```

2. **Run with vision** (agents see + use knowledge):
   ```bash
   python3 multi_agent_game.py --duration 5 --use-llm
   ```

## Progress Over Time

- **Episode 1**: Random behavior, basic heuristics
- **Episode 5**: Understands basic mechanics
- **Episode 10**: Strategic behavior emerges
- **Episode 20+**: Sophisticated manipulation

## Example: What Agent Learns

**Before Training:**
- "I should farm... maybe?"
- Random tool selection
- Doesn't understand risks

**After Training:**
- "I see brown soil → use hoe → plant seeds → harvest"
- "Trees are dangerous → avoid unless necessary"
- "Trader is at house → deliver for credit"
- "Others are doing risky work → I'll take credit"

## Quick Start

```bash
# Option 1: Vision (agents see game)
export OPENAI_API_KEY="your-key"
python3 multi_agent_game.py --duration 5 --use-llm

# Option 2: Training (build knowledge)
python3 train_agents.py --episodes 10

# Option 3: Both (best results)
python3 train_agents.py --episodes 10
python3 multi_agent_game.py --duration 5 --use-llm
```

Agents get smarter with each episode! 🧠
