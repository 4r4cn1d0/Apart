#!/bin/bash
# Quick setup for OpenAI API

echo "=========================================="
echo "OpenAI API Setup for Sprout Land"
echo "=========================================="
echo ""

# Check if API key is already set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Enter your OpenAI API key (starts with 'sk-'):"
    echo "Get one from: https://platform.openai.com/api-keys"
    echo ""
    read -p "API Key: " api_key
    
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided"
        exit 1
    fi
    
    export OPENAI_API_KEY="$api_key"
    echo ""
    echo "✅ API key set for this session"
    echo ""
    echo "To make it permanent, add to ~/.zshrc:"
    echo "  export OPENAI_API_KEY=\"$api_key\""
    echo ""
else
    echo "✅ API key already set: ${OPENAI_API_KEY:0:10}...${OPENAI_API_KEY: -4}"
    echo ""
fi

# Test connection
echo "Testing connection..."
cd "/Users/spiderishi/Coding/AI Manipulation/code"
python3 test_openai_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Run the game with:"
    echo "  cd '/Users/spiderishi/Coding/AI Manipulation/code'"
    echo "  export OPENAI_API_KEY=\"$OPENAI_API_KEY\""
    echo "  python3 main.py --ai --api openai"
    echo ""
fi
