#!/bin/bash
# Quick start script for AI-controlled game

cd "/Users/spiderishi/Coding/AI Manipulation/code"

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set!"
    echo ""
    echo "Run:"
    echo "  export OPENAI_API_KEY='sk-...'"
    echo ""
    echo "Or run the setup script:"
    echo "  ./setup_openai.sh"
    exit 1
fi

echo "Starting AI-controlled game..."
echo "API: OpenAI"
echo ""

python3 main.py --ai --api openai
