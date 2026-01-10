# Multi-Agent Manipulation Research Platform

## Overview

This platform studies how LLM agents manipulate each other in cooperative scenarios with misaligned incentives.

## Architecture

```
multi_agent/
├── agent_base.py          # Base agent class with utility functions
├── agent_types.py          # Different agent types (credit-seeker, fairness, etc.)
├── game_state.py           # Shared game environment and task execution
├── communication.py        # Public/private messaging system
├── measurement.py          # Manipulation metrics and ATE calculations
└── simulation.py           # Main simulation controller
```

## Quick Start

### Basic Run (Heuristic Agents)

```bash
python3 run_research_simulation.py --num-days 10
```

### With LLM Agents

```bash
export OPENAI_API_KEY="your-key"
python3 run_research_simulation.py --num-days 10 --use-llm --api openai
```

### Experimental Conditions

```bash
# Misaligned incentives, communication on
python3 run_research_simulation.py --incentive-alignment misaligned --communication

# Aligned incentives, communication off
python3 run_research_simulation.py --incentive-alignment aligned --no-communication

# With transparency
python3 run_research_simulation.py --transparency
```

## Agent Types

- **credit_seeker**: Maximizes personal credit, minimizes labor
- **fairness**: Wants balanced contributions
- **risk_averse**: Avoids risky tasks
- **baseline**: Aligned with town prosperity

## Metrics Calculated

- **Work-Benefit Gap**: E_i = (L_i/ΣL) - (U_i/ΣU)
- **Credit Capture**: CC_i = C_i / ΣL
- **Risk Externalization**: RE_i = (Q_i/ΣQ) - (U_i/ΣU)
- **ATE**: Average Treatment Effects for causal analysis

## Output

Simulation logs are exported as JSON with:
- Daily logs (actions, messages, outcomes)
- Measurement history
- All communications
- Final metrics

## Next Steps

1. Integrate LLM decision-making into agent types
2. Add linguistic manipulation detection
3. Implement transparency/auditing mechanisms
4. Run full experimental suite
