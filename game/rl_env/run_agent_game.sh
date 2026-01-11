#!/bin/bash
# Run the game with RL agent control (not keyboard control!)

SSH_KEY="$HOME/.ssh/id_ed25519"
HOST="ubuntu@209.20.157.218"
REMOTE_DIR="~/game/rl_env"
MODEL="models/ppo_sproutland_final.zip"

echo "=========================================="
echo "  RUNNING GAME WITH RL AGENT CONTROL"
echo "=========================================="
echo ""
echo "This will:"
echo "  ✓ Load the trained model (reward: +72.3!)"
echo "  ✓ Enable agent controls (use_agent_controls = True)"
echo "  ✓ Agent will control the player automatically"
echo "  ✓ You can WATCH the agent play"
echo "  ✗ Keyboard input will be IGNORED"
echo ""
echo "Starting evaluation..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && \
    source ~/game/venv/bin/activate && \
    export PYTHONPATH=\$HOME/game/code:\$PYTHONPATH && \
    python evaluate.py $MODEL --single --render --max-steps 3000 --max-days 10"

echo ""
echo "Evaluation complete!"
