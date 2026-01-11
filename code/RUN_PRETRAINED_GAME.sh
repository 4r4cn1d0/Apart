#!/bin/bash
# Run game with pre-trained agents (they know how to play!)

cd "/Users/spiderishi/Coding/AI Manipulation/code"

echo "=========================================="
echo "Multi-Agent Game - Pre-Trained Agents"
echo "=========================================="
echo ""
echo "✅ Agents have pre-loaded game knowledge!"
echo "   They know:"
echo "   - All game mechanics"
echo "   - Tool functions and controls"
echo "   - Locations and strategies"
echo "   - Their agent type objectives"
echo ""
echo "No learning needed - ready to play intelligently!"
echo ""
echo "Starting 5-minute episode..."
echo ""

python3 multi_agent_game.py --duration 5 --num-agents 4
