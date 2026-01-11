#!/bin/bash
# Launch Multi-Agent Manipulation Game

cd "/Users/spiderishi/Coding/AI Manipulation/code"

echo "=========================================="
echo "Multi-Agent Manipulation Research Game"
echo "=========================================="
echo ""
echo "This will run a 5-minute episode where:"
echo "  - 4 AI agents control the game"
echo "  - Agents communicate and make decisions"
echo "  - You'll see manipulation in action!"
echo ""
echo "Press ESC to exit early"
echo ""

python3 multi_agent_game.py --duration 5 --num-agents 4
