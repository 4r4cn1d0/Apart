#!/bin/bash

# Start Agent Training
# Trains agents with critic-based rewards (triforce-style)

echo "=========================================="
echo "Starting Agent Training"
echo "=========================================="
echo ""

# Default parameters (adjustable)
EPISODES=${1:-30}
DURATION=${2:-3}
DAYS=${3:-3}

echo "Configuration:"
echo "  Episodes: $EPISODES"
echo "  Duration: $DURATION minutes per day"
echo "  Days per episode: $DAYS"
echo "  Estimated time: ~$((EPISODES * DURATION * DAYS / 60)) hours"
echo ""

# Check for Lambda API (optional)
if [ -n "$LAMBDA_API_URL" ] && [ -n "$LAMBDA_API_KEY" ]; then
    echo "✅ Lambda API configured - will use if --use-lambda flag is set"
    LAMBDA_FLAGS="--use-lambda --lambda-url $LAMBDA_API_URL --lambda-key $LAMBDA_API_KEY"
else
    echo "ℹ️  Lambda API not configured - using heuristic agents (faster)"
    LAMBDA_FLAGS=""
fi

echo ""
echo "Starting training..."
echo "Press Ctrl+C to stop (progress will be saved)"
echo ""

# Run training
python3 train_game_agents.py \
    --episodes $EPISODES \
    --duration $DURATION \
    --days $DAYS \
    $LAMBDA_FLAGS

echo ""
echo "=========================================="
echo "Training Complete!"
echo "=========================================="
echo ""
echo "Results saved to:"
echo "  - training_output/training_metrics_*.json"
echo "  - agent_memory.json"
echo ""
echo "Run game with trained agents:"
echo "  python3 multi_agent_game.py --num-agents 4"
echo ""
