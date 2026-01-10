# Setup Guide: Chat-Based Manipulation Research

## Quick Setup for Lambda Labs API

### 1. Get Lambda Labs API Credentials

If you don't have them yet:
- Sign up at https://cloud.lambda.ai
- Get your API key from the dashboard
- Note your instance IP if using direct instance access

### 2. Set Environment Variables

```bash
# For direct instance (no auth needed)
export LAMBDA_API_URL="http://YOUR_INSTANCE_IP:8000"

# OR for cloud API (requires key)
export LAMBDA_API_URL="https://cloud.lambda.ai/api/v1"
export LAMBDA_API_KEY="your_api_key_here"

# Optional: Specify model (defaults to 8B Instruct)
export LAMBDA_MODEL="meta-llama/Meta-Llama-3.1-8B-Instruct"
```

### 3. Run the Chat System

**Option A: With Lambda (LLM-powered agents)**
```bash
python3 manipulation_chat.py --use-lambda --days 5
```

**Option B: Without Lambda (heuristic agents)**
```bash
python3 manipulation_chat.py --days 5
```

**Option C: Using the script**
```bash
./run_manipulation_chat.sh
```

### 4. Test Lambda Connection

```bash
python3 -c "
from manipulation_chat import LambdaChatClient
import os

client = LambdaChatClient(
    api_url=os.getenv('LAMBDA_API_URL', 'http://192.222.59.32:8000'),
    api_key=os.getenv('LAMBDA_API_KEY')
)

response = client.chat([
    {'role': 'user', 'content': 'Say hello in one sentence.'}
], system_prompt='You are a helpful assistant.')

print('✅ Lambda API working!' if '[Error' not in response else f'❌ Error: {response}')
print(f'Response: {response}')
"
```

## What You'll See

When running, you'll see:

1. **Communication Phase**: Agents send messages to each other
2. **Action Decision Phase**: Each agent decides what action to take
3. **Manipulation Metrics**: Analysis of manipulation attempts

Example output:
```
======================================================================
DAY 1 - Chat-Based Manipulation Research
======================================================================

📢 COMMUNICATION PHASE
----------------------------------------------------------------------
credit_seeker_1: I think mining could be a great opportunity...
risk_averse_1: I'm not really comfortable with high-risk tasks...
fairness_1: We should make sure everyone contributes fairly...

🎯 ACTION DECISION PHASE
----------------------------------------------------------------------
credit_seeker_1 chose: deliver
risk_averse_1 chose: farm
fairness_1 chose: farm
baseline_1 chose: mine

Manipulation Analysis Summary:
  Risk shift attempts: 1
  Credit capture attempts: 1
  Persuasion attempts: 2
```

## Output Files

Logs are saved as JSON:
- `manipulation_chat_log_YYYYMMDD_HHMMSS.json`

Contains:
- All messages from each day
- Actions taken by each agent
- Manipulation metrics

## Troubleshooting

### Lambda API Not Working

1. **Check API URL**: Make sure it's correct
   - Direct instance: `http://IP:PORT`
   - Cloud API: `https://cloud.lambda.ai/api/v1`

2. **Check API Key**: Required for cloud API, not needed for direct instance

3. **Test Connection**:
   ```bash
   curl http://YOUR_INSTANCE_IP:8000/v1/models
   # Should return list of models
   ```

4. **Check Model**: Make sure model name is correct
   - Text models: `meta-llama/Meta-Llama-3.1-8B-Instruct`
   - Not vision models for chat

### Fallback to Heuristics

If Lambda doesn't work, the system automatically falls back to rule-based agents (no API needed). These still demonstrate manipulation patterns.

## Next Steps

1. Run multiple scenarios with different agent combinations
2. Analyze the JSON logs for manipulation patterns
3. Compare LLM-based vs heuristic agents
4. Use findings to inform game-based research
5. Build visualization tools for manipulation emergence

## Example Use Cases

### Study Credit Seeking
```bash
# Create scenario with multiple credit seekers
python3 manipulation_chat.py --use-lambda --days 10
```

### Study Risk Aversion
```bash
# More risk-averse agents
# (Modify create_agent_profiles() to add more risk-averse agents)
```

### Compare LLM vs Heuristics
```bash
# Run with Lambda
python3 manipulation_chat.py --use-lambda --days 5 > llm_log.txt

# Run without Lambda
python3 manipulation_chat.py --days 5 > heuristic_log.txt

# Compare outputs
```
