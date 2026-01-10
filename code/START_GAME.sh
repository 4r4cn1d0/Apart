#!/bin/bash
# Start Multi-Agent Game - 5 days continuous, 5 minutes per day

cd "$(dirname "$0")"

echo "=================================="
echo "Starting Multi-Agent Game"
echo "=================================="
echo "Configuration:"
echo "  - 4 agents (Credit Seeker, Fairness, Risk Averse, Baseline)"
echo "  - 5 days continuous"
echo "  - 5 minutes per day"
echo "  - Total time: ~25 minutes"
echo ""
echo "Controls:"
echo "  - Drag mouse to move camera (free cam)"
echo "  - ESC to exit"
echo ""
echo "Agents will:"
echo "  - Move around the map"
echo "  - Use tools (hoe, axe, water)"
echo "  - Plant seeds and harvest"
echo "  - Interact with objects"
echo "  - Communicate with each other"
echo ""
echo "Starting game in 3 seconds..."
sleep 3

python3 multi_agent_game.py --num-agents 4
