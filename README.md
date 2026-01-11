# AI Manipulation - Multi-Agent Farming Game

A Pygame-based farming simulation game with multi-agent manipulation research capabilities.

## Features

- **Multi-Agent System**: 4 agent types (credit_seeker, fairness, risk_averse, baseline)
- **Training System**: Visible and headless training modes with persistent memory
- **Learning**: Agents learn from experiences and build knowledge patterns
- **Triforce-Inspired Critics**: Structured reward system for training
- **API Support**: OpenAI, Anthropic, and Lambda Labs integration
- **Research Framework**: Built for studying manipulation in multi-agent environments

## Quick Start

### Install Dependencies
```bash
pip3 install pygame pytmx requests
```

### Run Training (Visible Mode)
```bash
cd code
python3 train_game_agents.py --episodes 100 --duration 1 --days 2
```

### Run Game with Agents
```bash
cd code
python3 multi_agent_game.py --num-agents 4
```

## Project Structure

```
├── code/                    # Main game and training code
│   ├── multi_agent/        # Multi-agent system components
│   ├── agent_memory.json   # Persistent learning data
│   └── train_game_agents.py # Training system
├── data/                    # Game map and tilesets
├── graphics/                # Game assets
└── audio/                   # Sound effects (disabled)

```

## Documentation

- `code/LEARNING_FILE_LOCATIONS.md` - Where actions are recorded
- `code/TRAINING_GUIDE.md` - Training system guide
- `code/AGENT_MEMORY.md` - Memory system documentation
- `code/RESEARCH_DESIGN.md` - Research framework details

## Status

✅ Code ready and committed  
🔐 Authentication needed to push to GitHub

See authentication instructions in terminal output.
