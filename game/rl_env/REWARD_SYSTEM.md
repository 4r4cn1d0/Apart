# Comprehensive Cycle-Based Reward System

## Overview
This reward system is designed to properly incentivize complete farming cycles and penalize incomplete or abandoned cycles. The agent must learn to execute the full sequence: **Till → Water → Plant → Wait → Harvest → Sell**.

## Core Philosophy
- **Major rewards for complete cycles** (5.0 points)
- **Small rewards for cycle steps** (0.1 each)
- **Penalties for incomplete cycles** (-1.0 points)
- **Profit-based scaling** (rewards scale with actual money earned)

## Reward Structure

### 1. Complete Farming Cycle Rewards
**Complete Cycle Bonus: +5.0 points**
- Awarded when: Till → Water → Plant → Harvest sequence is completed
- This is the PRIMARY reward mechanism
- Encourages the agent to finish what it starts

**Cycle Efficiency Bonus: +2.0 points**
- Awarded if cycle completed in < 200 steps
- Encourages efficient gameplay

**Cycle Profit Bonus: +0.2 × profit**
- Additional bonus based on money earned from selling crops
- Scales with actual profit (corn=$6, tomato=$15)

### 2. Individual Action Rewards
- **Till Success: +0.1** - Small reward for tilling
- **Water Success: +0.1** - Small reward for watering  
- **Plant Success: +0.1** - Small reward for planting
- **Harvest: +0.5** - Moderate reward for harvesting
- **Cycle Progress Bonus: +0.05** - Small bonus for each step in cycle

### 3. Selling and Money Rewards
**Sell Bonus: +0.2**
- Reward for selling items (encourages selling crops)

**Sell Profit Bonus: +0.15 × profit**
- Scales with actual profit from sale
- Corn: $10 sale = +1.5 bonus
- Tomato: $20 sale = +3.0 bonus

**Money Scale: +0.05 × money_delta**
- General reward for earning money
- Encourages profit-making activities

### 4. Incomplete Cycle Penalties
**Incomplete Cycle Penalty: -1.0 points**
- Applied when a cycle is started but abandoned
- Abandonment threshold: 500 steps without progress
- Discourages starting cycles without finishing

### 5. Action Spam Penalties
**Invalid Action Penalty: -0.1**
- Heavy penalty for invalid actions (e.g., planting with no seeds)

**Idle Penalty: -0.002 per step after 50 idle steps**
- Penalizes doing nothing for too long
- Threshold reduced from 100 to 50 steps

### 6. Resource Collection
- **Apple Collect: +0.1**
- **Wood Collect: +0.2**

### 7. Seed Management
- **Buy Seed: +0.05** - Small reward for buying seeds
- **Low Seed Purchase Bonus: +0.3** - Bonus when inventory < 3 seeds
- Encourages proactive seed management

### 8. Diversity and Preferences
- **Diversity Bonus: +1.0** - Reward for growing both corn and tomato
- **Tomato Preference: +0.1** - Small bonus for tomato (higher value)

### 9. Day Completion
- **Day Complete Bonus: +0.5** - Reward for completing a day

## Cycle Tracking

The system tracks:
- **Cycle Start**: When first action (till/water/plant) occurs
- **Cycle Progress**: Each step in the cycle updates progress timestamp
- **Cycle Completion**: Harvest with all previous steps completed
- **Cycle Abandonment**: 500 steps without progress = abandoned

## Expected Behavior

With this reward system, the agent should learn to:
1. **Start cycles intentionally** (not randomly)
2. **Complete cycles** (major reward at end)
3. **Sell crops** (profit-based rewards)
4. **Buy seeds proactively** (before running out)
5. **Avoid abandoning cycles** (penalty for incomplete cycles)
6. **Work efficiently** (efficiency bonus for fast cycles)

## Reward Scale Comparison

**Complete Cycle with Sale:**
- Till: +0.1
- Water: +0.1
- Plant: +0.1
- Harvest: +0.5
- Cycle Completion: +5.0
- Efficiency Bonus: +2.0 (if fast)
- Sell: +0.2
- Profit Bonus: +0.15 × profit
- **Total: ~8.0-10.0 points per complete cycle**

**Incomplete Cycle (abandoned):**
- Till: +0.1
- Water: +0.1
- Plant: +0.1
- Abandonment Penalty: -1.0
- **Total: -0.7 points (net negative!)**

This creates a strong incentive to complete cycles rather than abandon them.

## Training Implications

The agent will need to:
- Learn action sequences (not just individual actions)
- Understand cooldowns (via improved action masking)
- Plan ahead (buy seeds before running out)
- Be efficient (complete cycles quickly)
- Avoid action spam (penalties for invalid actions)

This reward structure should lead to much better gameplay than the previous system that rewarded action spamming.
