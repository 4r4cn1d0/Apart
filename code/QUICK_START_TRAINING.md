# Quick Start: Training Agents to Play the Game

## Option 1: Vision-Based Agents (Recommended)

Agents can see the game and learn naturally:

```bash
# Set your API key
export OPENAI_API_KEY="your-key"
# Or for Lambda:
export LAMBDA_API_URL="http://192.222.59.32:8000"

# Run game with vision-enabled agents
python3 multi_agent_game.py --duration 5 --use-llm --api openai
```

**What happens:**
- Agents see the game screen every decision
- They understand game mechanics visually
- They learn what works through experience
- Each episode makes them smarter

## Option 2: Training Episodes

Run training episodes to build knowledge:

```bash
# Run 10 training episodes
python3 train_agents.py --episodes 10

# This creates:
# - training_data/ (episode logs)
# - agent_knowledge.json (learned patterns)
```

**What agents learn:**
- Successful action sequences
- Effective communication strategies
- Risk assessment patterns
- Resource management

## Option 3: Combined Approach

1. **Train first** (build knowledge base):
   ```bash
   python3 train_agents.py --episodes 20
   ```

2. **Run with vision** (agents use both):
   ```bash
   python3 multi_agent_game.py --duration 5 --use-llm
   ```

## What Makes Agents "Know" the Game

### Vision-Based Understanding
- **See game state**: Agents see where objects are
- **Understand mechanics**: Learn tool usage visually
- **Context-aware**: Make decisions based on what they see

### Learned Patterns
- **Successful strategies**: What actions lead to success
- **Communication**: What messages work
- **Risk assessment**: When to take/avoid risks

### Game Knowledge Base
- **Tool functions**: What each tool does
- **Location mapping**: Where important objects are
- **Action outcomes**: What happens from each action

## Progress Tracking

Agents get better over time:
- **Episode 1**: Random/naive behavior
- **Episode 5**: Basic understanding
- **Episode 10**: Strategic behavior
- **Episode 20+**: Sophisticated manipulation

## Tips

1. **More episodes = smarter agents**
2. **Vision agents learn faster** (see what works)
3. **Training data improves future runs**
4. **Combine both methods** for best results

Run more episodes to see agents get smarter! 🧠
