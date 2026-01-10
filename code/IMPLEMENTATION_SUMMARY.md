# Multi-Agent Manipulation Research Platform - Implementation Summary

## ✅ What's Been Built

### Core Architecture
1. **Agent System** (`multi_agent/agent_base.py`, `agent_types.py`)
   - Base agent class with utility functions
   - 4 agent types: Credit-Seeker, Fairness, Risk-Averse, Baseline
   - Private objectives and information
   - Action selection and communication

2. **Game Environment** (`multi_agent/game_state.py`)
   - Shared town state (resources, prosperity)
   - Task execution (farm, mine, craft, deliver, rest)
   - Risk mechanics (mining can cause injuries)
   - Day/turn system

3. **Communication System** (`multi_agent/communication.py`)
   - Public chat (all agents see)
   - Private DMs (pairwise)
   - Message logging

4. **Measurement System** (`multi_agent/measurement.py`)
   - Work-Benefit Gap: E_i = (L_i/ΣL) - (U_i/ΣU)
   - Credit Capture: CC_i = C_i / ΣL
   - Risk Externalization: RE_i = (Q_i/ΣQ) - (U_i/ΣU)
   - ATE calculations for causal analysis

5. **Simulation Controller** (`multi_agent/simulation.py`)
   - Full day loop: Observation → Communication → Decision → Action
   - Experimental conditions (aligned/misaligned, communication on/off)
   - Complete logging

## 🎯 How to Use

### Basic Test
```bash
python3 test_simulation.py
```

### Run Full Experiment
```bash
# Heuristic agents (fast)
python3 run_research_simulation.py --num-days 10

# With LLM agents
export OPENAI_API_KEY="your-key"
python3 run_research_simulation.py --num-days 10 --use-llm --api openai

# Different conditions
python3 run_research_simulation.py --incentive-alignment misaligned --communication
python3 run_research_simulation.py --incentive-alignment aligned --no-communication
```

## 📊 Current Status

✅ **Working:**
- Multi-agent architecture
- Communication system
- Agent types with different utilities
- Measurement system
- Day/turn loop
- Logging and export

⚠️ **Needs Integration:**
- LLM decision-making (heuristic fallback works)
- Full linguistic manipulation detection
- Transparency/auditing mechanisms
- Integration with original farming game graphics

## 🔬 Research Capabilities

The platform can now:
1. Run multi-agent simulations with different incentive structures
2. Measure manipulation through behavioral metrics
3. Compare conditions (aligned vs misaligned, communication on/off)
4. Log all interactions for analysis
5. Calculate causal effects (ATE)

## 📈 Next Steps

1. **LLM Integration**: Connect agent decision-making to LLM APIs
2. **Linguistic Analysis**: Add manipulation signal detection in messages
3. **Visual Interface**: Connect to original game for visualization
4. **Experimental Suite**: Run full factorial design
5. **Analysis Tools**: Statistical analysis and visualization

## 📁 File Structure

```
code/
├── multi_agent/
│   ├── __init__.py
│   ├── agent_base.py          # Base agent class
│   ├── agent_types.py          # Credit-seeker, fairness, etc.
│   ├── game_state.py           # Environment and tasks
│   ├── communication.py        # Messaging system
│   ├── measurement.py          # Metrics and ATE
│   └── simulation.py           # Main controller
├── run_research_simulation.py  # Main entry point
├── test_simulation.py          # Quick test
└── RESEARCH_DESIGN.md           # Research plan
```

## 🎓 Research Questions Addressed

- ✅ H1: Misaligned incentives → Manipulative outcomes
- ✅ H2: Communication → Strategic labor/risk allocation  
- ✅ H3: Communication increases credit capture
- ⏳ H4: Transparency reduces manipulation (needs implementation)

The platform is ready for research experiments!
