# AI Agent Control for Sprout Land

This game now supports AI-controlled gameplay using vision-based AI models!

## Setup

### 1. Install Dependencies

```bash
pip install pillow openai anthropic requests
```

Or for a specific provider:
- OpenAI: `pip install openai pillow`
- Anthropic: `pip install anthropic pillow`
- Lambda Labs: `pip install requests pillow`

### 2. Set API Key

Set your API key as an environment variable:

**OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Anthropic:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Lambda Labs:**
```bash
export LAMBDA_API_KEY="your-api-key-here"
```

### 3. Run with AI Control

**Using OpenAI (default):**
```bash
python main.py --ai --api openai
```

**Using Anthropic Claude:**
```bash
python main.py --ai --api anthropic
```

**Using Lambda Labs:**
```bash
python main.py --ai --api lambda
```

**With API key as argument:**
```bash
python main.py --ai --api openai --api-key "your-key-here"
```

**Manual control (default):**
```bash
python main.py
```

## How It Works

1. **Screenshot Capture**: The AI agent captures screenshots of the game every N frames
2. **Vision Analysis**: Screenshots are sent to the vision API along with game state information
3. **Action Decision**: The AI analyzes the screen and decides on the best action
4. **Execution**: Actions are executed automatically (movement, tool use, planting, etc.)

## Available Actions

The AI can perform:
- **Movement**: `move_up`, `move_down`, `move_left`, `move_right`, `move_none`
- **Tools**: `use_tool` (hoe/axe/water), `switch_tool`
- **Seeds**: `use_seed` (plant), `switch_seed`
- **Interactions**: `interact` (shop/bed)

## Configuration

You can adjust AI behavior in `ai_agent.py`:
- `decision_interval`: How often the AI makes decisions (default: every 10 frames)
- `max_size`: Maximum screenshot size to reduce API costs (default: 1024px)

## Cost Optimization

- Screenshots are automatically resized to reduce API costs
- Decisions are made every N frames (not every frame)
- Consider using cheaper models or reducing decision frequency for longer sessions

## Troubleshooting

**"API key not found"**: Make sure you've set the environment variable or passed `--api-key`

**"Module not found"**: Install the required packages for your chosen API provider

**AI not responding**: Check your API key is valid and you have credits/quota remaining

**Performance issues**: Increase `decision_interval` in `ai_agent.py` to reduce API calls
