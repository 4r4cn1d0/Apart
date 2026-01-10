# Quick Start: AI Agent Control

## For Lambda Labs Users

If you have Lambda credits, you can use Lambda Labs API:

1. **Get your API key** from Lambda Labs dashboard
2. **Set environment variable:**
   ```bash
   export LAMBDA_API_KEY="your-lambda-api-key"
   ```
3. **Run the game:**
   ```bash
   python main.py --ai --api lambda
   ```

## For OpenAI Users

1. **Get API key** from https://platform.openai.com
2. **Set environment variable:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
3. **Run:**
   ```bash
   python main.py --ai --api openai
   ```

## For Anthropic Users

1. **Get API key** from https://console.anthropic.com
2. **Set environment variable:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
3. **Run:**
   ```bash
   python main.py --ai --api anthropic
   ```

## Testing

To test if everything works, run without `--ai` first to make sure the game loads:
```bash
python main.py
```

Then enable AI mode and watch the AI play!

## Tips

- The AI makes decisions every 10 frames by default (adjustable in `ai_agent.py`)
- Screenshots are automatically resized to save API costs
- You can press ESC or close the window to stop
- The AI will try to farm efficiently: till soil, plant seeds, water crops, harvest, and sell items
