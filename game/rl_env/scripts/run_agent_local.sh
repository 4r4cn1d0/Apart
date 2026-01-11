#!/bin/bash
# Run the agent-controlled game locally with rendering

cd "$(dirname "$0")/../.." || exit 1
SCRIPT_DIR="$(pwd)"

echo "=========================================="
echo "  RUNNING AGENT-CONTROLLED GAME LOCALLY"
echo "=========================================="
echo ""
echo "This will:"
echo "  ✓ Load the trained model locally"
echo "  ✓ Enable agent controls"
echo "  ✓ Show the game window with agent playing"
echo "  ✓ You can WATCH the agent play in real-time"
echo ""

# Check dependencies
echo "Checking dependencies..."
python3 -c "import stable_baselines3" 2>/dev/null || {
    echo "✗ stable_baselines3 not installed"
    echo "  Installing..."
    pip3 install stable-baselines3[extra] || exit 1
}

python3 -c "import pytmx" 2>/dev/null || {
    echo "✗ pytmx not installed"
    echo "  Installing..."
    pip3 install pytmx || exit 1
}

python3 -c "import pygame" 2>/dev/null || {
    echo "✗ pygame not installed"
    echo "  Installing..."
    pip3 install pygame || exit 1
}

echo "✓ All dependencies installed"
echo ""

# Set up Python path
export PYTHONPATH="$SCRIPT_DIR/code:$PYTHONPATH"

# Change to rl_env directory
cd "$SCRIPT_DIR/rl_env" || exit 1

# Run evaluation with rendering
echo "Starting agent-controlled game..."
echo "Press Ctrl+C to stop"
echo ""

python3 evaluate.py models/ppo_sproutland_final.zip --single --render --max-steps 3000 --max-days 10

echo ""
echo "Evaluation complete!"
