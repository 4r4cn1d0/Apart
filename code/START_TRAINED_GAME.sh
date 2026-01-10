#!/bin/bash
# Start game with trained/vision-enabled agents

cd "/Users/spiderishi/Coding/AI Manipulation/code"

echo "=========================================="
echo "Multi-Agent Game with Vision/Training"
echo "=========================================="
echo ""

# Check for API key
if [ -z "$OPENAI_API_KEY" ] && [ -z "$LAMBDA_API_URL" ]; then
    echo "⚠️  No API key found. Agents will use heuristic behavior."
    echo ""
    echo "For vision-enabled agents (agents can see the game):"
    echo "  export OPENAI_API_KEY='your-key'"
    echo "  OR"
    echo "  export LAMBDA_API_URL='http://192.222.59.32:8000'"
    echo ""
    read -p "Continue with heuristic agents? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_LLM=""
    API=""
else
    USE_LLM="--use-llm"
    if [ -n "$LAMBDA_API_URL" ]; then
        API="--api lambda"
    else
        API="--api openai"
    fi
    echo "✅ Using vision-enabled agents!"
    echo "   Agents can see the game and learn from it!"
    echo ""
fi

echo "Starting 5-minute episode..."
echo "Agents will learn and improve as they play!"
echo ""

python3 multi_agent_game.py --duration 5 --num-agents 4 $USE_LLM $API
