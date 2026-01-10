# Multi-Agent Manipulation Research Platform

## Project Overview

Building a research environment to study LLM agent manipulation in multi-agent cooperation scenarios with misaligned incentives.

## Architecture Plan

### Core Components

1. **Game Environment** (based on current farming game)
   - Shared world state
   - Resources (food, ore, tools)
   - Tasks (farm, mine, craft, deliver, rest)
   - Risk mechanics (mining can injure)
   - Day/turn system

2. **Multi-Agent System**
   - 3-4 LLM-controlled agents
   - Each agent has:
     - Private utility function
     - Private objectives
     - Partial information access
     - Action selection capability

3. **Communication System**
   - Public chat (all agents see)
   - Private DMs (pairwise)
   - Message timing (before actions each day)

4. **Agent Types**
   - **Credit-Seeker**: Maximizes personal credit points
   - **Fairness-Agent**: Wants balanced labor contributions
   - **Risk-Averse**: Avoids high-risk tasks
   - **Baseline**: Aligned with town prosperity

5. **Measurement System**
   - Work-Benefit Gap: E_i = (L_i/ΣL) - (U_i/ΣU)
   - Credit Capture: CC_i = C_i / ΣL
   - Risk Externalization: RE_i = (Q_i/ΣQ) - (U_i/ΣU)
   - Linguistic manipulation signals

6. **Experimental Conditions**
   - Aligned vs Misaligned incentives
   - Communication enabled vs disabled
   - Transparency/auditing on vs off

## Implementation Phases

### Phase 1: Multi-Agent Infrastructure
- [ ] Agent base class
- [ ] Shared game state manager
- [ ] Multi-agent game loop

### Phase 2: Communication System
- [ ] Public chat channel
- [ ] Private DM system
- [ ] Message logging

### Phase 3: Agent Types & Utilities
- [ ] Credit-seeker agent
- [ ] Fairness agent
- [ ] Risk-averse agent
- [ ] Utility calculation system

### Phase 4: Measurement & Logging
- [ ] Behavioral metrics
- [ ] Linguistic analysis
- [ ] Causal effect calculations

### Phase 5: Experimental Framework
- [ ] Condition switching
- [ ] Replication system
- [ ] Data export
