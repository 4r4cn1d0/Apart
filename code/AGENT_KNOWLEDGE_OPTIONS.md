# Getting Agents to Know the Game: Options & Approach

## Current Status ✅

We've removed detailed instructions from prompts. Agents now use **observation-based learning** - they see the game screen and figure out mechanics through trial and error.

## The Challenge

LLMs **cannot be retrained during runtime**. Once a model is loaded, its weights are fixed. So we can't "teach" agents new knowledge by modifying the model itself.

## Options for Game Knowledge

### ✅ Option 1: Observation-Based (CURRENT APPROACH)
**How it works:**
- Agents see game screenshots via vision models
- They observe their actions and outcomes
- Learn through experience during gameplay

**Pros:**
- Works immediately, no setup
- Agents adapt to actual game state
- Minimal prompts (no detailed instructions)

**Cons:**
- Learning is slower - takes time to understand mechanics
- Early episodes may have poor performance
- Requires vision-capable LLMs

**Status:** ✅ Implemented - agents learn by playing

---

### Option 2: Few-Shot Learning (Examples in Context)
**How it works:**
- Include 2-5 example gameplay sequences in prompts
- Show successful action sequences: "When I see brown soil, I use hoe, then plant seed"
- Update examples based on what works

**Pros:**
- Faster learning than pure observation
- Can demonstrate specific mechanics
- Still minimal (just examples, not manuals)

**Cons:**
- Examples take up context tokens
- Need to curate good examples
- Examples may not match current situation

**Implementation:**
```python
examples = """
Example 1: See brown soil → use hoe → plant seed → harvest → success
Example 2: See tree → use axe → get wood → deliver → success  
"""
prompt = f"{examples}\n\nNow observe the screen and decide..."
```

**Status:** Can be added - would improve learning speed

---

### Option 3: Training Knowledge Base (RECOMMENDED)
**How it works:**
1. Run training episodes (agents play game)
2. Record successful action patterns
3. Save to knowledge base file
4. Include minimal summaries in prompts going forward

**Pros:**
- Builds knowledge from actual gameplay
- Can be updated after each session
- Minimal prompts (just patterns, not instructions)
- Agents "remember" what worked before

**Cons:**
- Requires running training episodes first
- Knowledge base needs to be maintained

**Status:** ✅ Implemented in `train_on_game.py`

**Usage:**
```bash
# Train agents on game
python3 train_on_game.py --episodes 5 --duration 2 --use-llm

# Then run game - agents will use learned patterns
python3 multi_agent_game.py --duration 5 --num-agents 4
```

---

### Option 4: Fine-Tuning (ADVANCED)
**How it works:**
1. Collect gameplay demonstrations (100s-1000s of examples)
2. Fine-tune LLM on this data
3. Deploy fine-tuned model
4. Agents now have game knowledge "baked in"

**Pros:**
- Agents know game mechanics from start
- No context needed for knowledge
- Can be very effective

**Cons:**
- Requires fine-tuning infrastructure (GPUs, compute)
- Expensive (API costs or compute time)
- Time-consuming (hours to days)
- Need large dataset of good demonstrations

**Status:** Not implemented - would require:
- Fine-tuning API (OpenAI, Anthropic, or self-hosted)
- Large dataset of gameplay demonstrations
- Significant compute resources

---

## Recommended Approach

**For immediate use (right now):**
1. ✅ **Observation-based learning** - agents learn by playing (current)
2. ✅ **Training knowledge base** - run `train_on_game.py` to build patterns
3. ⚠️ **Few-shot examples** - can add if learning is too slow

**For best results (with more time):**
1. Run training episodes to build knowledge base
2. Include few-shot examples from knowledge base
3. Let agents continue learning through observation
4. Optionally: Fine-tune if you have resources

---

## What We've Done

✅ Removed detailed game manual from prompts  
✅ Made prompts minimal and observation-based  
✅ Created training script to build knowledge base  
✅ Agents now learn through gameplay experience  

## Next Steps

1. **Run training now:**
   ```bash
   cd code
   python3 train_on_game.py --episodes 3 --duration 2 --use-llm --api lambda
   ```

2. **Then run game with trained knowledge:**
   ```bash
   python3 multi_agent_game.py --duration 5 --num-agents 4 --use-llm --api lambda
   ```

3. **Agents will:**
   - Use learned patterns from training
   - Continue learning through observation
   - Improve over time

---

## Summary

**Agents know the game through:**
1. **Vision** - seeing the game screen (immediate)
2. **Experience** - playing and learning (ongoing)
3. **Knowledge base** - patterns from training episodes (if you run training)

**Not through:**
- ❌ Detailed instruction manuals (removed per your request)
- ❌ Retraining model weights (not possible during runtime)
- ❌ Static knowledge embedded in model (would require fine-tuning)

**To get agents to "know exactly how the game works":**
- Run training episodes first to build knowledge base
- Agents will use this + observation during gameplay
- This is the best balance between "no detailed instructions" and "agents know the game"
