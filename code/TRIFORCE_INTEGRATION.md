# Triforce Integration - Farming Game Agent System

This document describes the integration of concepts from the [triforce](https://github.com/DarkAutumn/triforce) Zelda NES agent project into the farming game multi-agent system.

## Overview

The triforce project uses a sophisticated reward/critic system, observation wrappers, and scenario-based training. We've adapted these concepts for the farming game agent training system.

## Key Components

### 1. Critics (`multi_agent/farming_critics.py`)

Similar to triforce's `ZeldaCritic` classes, our critics evaluate actions and provide reward dictionaries:

- **ProsperityCritic**: Rewards actions that increase town prosperity
- **CreditCritic**: Rewards credit-gaining actions (for credit-seeking agents)
- **SafetyCritic**: Penalizes risky actions and rewards safe behavior
- **EfficiencyCritic**: Rewards efficient resource gathering
- **FairnessCritic**: Rewards balanced contributions
- **CompositeCritic**: Combines all critics (main critic used in training)

Each critic returns a **reward dictionary** (not just a scalar), allowing for detailed reward debugging and analysis, just like triforce.

### 2. Observation Wrapper (`multi_agent/observation_wrapper.py`)

Similar to triforce's `ObservationWrapper`, this converts game state into structured observations:

- **FarmingObservationWrapper**: Extracts viewport around player, maintains frame history, includes state features
- **ObjectiveWrapper**: Provides goal information to agents (similar to triforce's Objectives system)

### 3. Training Scenarios (`multi_agent/training_scenarios.py`)

Similar to triforce's scenario system:

- **TrainingScenario**: Defines training conditions, critics, agent types, and state overrides
- Predefined scenarios:
  - `baseline`: Standard cooperative scenario
  - `credit_seeker`: Credit-seeking agents
  - `manipulation`: Mixed incentives to study manipulation
  - `safe_farming`: No-risk scenario
  - `high_risk`: High-risk scenario

### 4. Integration with Existing System

The critics are integrated into the existing memory/learning system:

- Critics evaluate each action and provide rewards
- Rewards are stored in the memory system alongside outcomes
- Agents can use reward-based patterns for decision-making
- Visual feedback shows when agents use learned knowledge

## Usage

### Running with Critics

The game automatically initializes critics when started:

```bash
python3 multi_agent_game.py --num-agents 4
```

Critics will evaluate actions and rewards are stored in memory.

### Creating Custom Scenarios

```python
from multi_agent.training_scenarios import TrainingScenario, CompositeCritic

scenario = TrainingScenario(
    name="my_scenario",
    critic=CompositeCritic(agent_type="credit_seeker"),
    agent_types=["credit_seeker", "baseline"],
    max_days=10,
    description="My custom scenario"
)
```

### Using Critics in Code

```python
from multi_agent.farming_critics import CompositeCritic

critic = CompositeCritic(agent_type="credit_seeker")
rewards = critic.evaluate(prev_state, next_state, action, agent_type)
total_reward = critic.get_total_reward(rewards)
```

## Differences from Triforce

While inspired by triforce, our implementation is adapted for the farming game:

1. **Action Space**: Farming actions (farm, mine, deliver, rest) instead of Zelda actions
2. **State Representation**: Farming game state (inventory, prosperity, etc.) instead of Zelda game state
3. **Training**: Currently uses heuristic agents + memory, not deep RL (though structure is ready for RL)
4. **Scenarios**: Farming-specific scenarios instead of Zelda dungeons

## Future Enhancements

The structure is ready for:

1. **Deep RL Training**: Replace heuristics with neural network policies
2. **More Sophisticated Critics**: Add critics for communication, manipulation detection
3. **Scenario Variations**: More scenarios for manipulation research
4. **Evaluation System**: Similar to triforce's `evaluate.py` for measuring agent performance

## References

- [Triforce GitHub](https://github.com/DarkAutumn/triforce) - Original Zelda NES agent project
- Triforce uses critics, observation wrappers, and scenarios for training
- Our implementation adapts these concepts for multi-agent farming simulation
