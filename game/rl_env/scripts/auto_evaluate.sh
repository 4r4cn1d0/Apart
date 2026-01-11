#!/bin/bash
# Auto-evaluation script - waits for training to complete, then evaluates model

SSH_KEY="$HOME/.ssh/id_ed25519"
HOST="ubuntu@209.20.157.218"
REMOTE_DIR="~/game/rl_env"
FINAL_MODEL="models/ppo_sproutland_final.zip"

echo "========================================="
echo "  Auto-Evaluation Monitor"
echo "========================================="
echo ""
echo "Waiting for training to complete..."
echo "Monitoring for: $FINAL_MODEL"
echo ""

# Check if training is still running
while ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && ps aux | grep -E 'python.*train_ppo' | grep -v grep > /dev/null"; do
    # Training still running
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && tail -20 training_h100_8x.log 2>/dev/null | grep -E 'total_timesteps|iterations' | tail -1" || true
    sleep 30
done

echo ""
echo "Training complete! Checking for model..."
echo ""

# Wait for model to be saved (max 2 minutes)
max_wait=120
wait_time=0
while [ $wait_time -lt $max_wait ]; do
    if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && test -f $FINAL_MODEL"; then
        echo "✓ Model found! Starting evaluation..."
        echo ""
        
        # Run evaluation with rendering
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && \
            source ~/game/venv/bin/activate && \
            export PYTHONPATH=\$HOME/game/code:\$PYTHONPATH && \
            python evaluate.py $FINAL_MODEL --single --render --max-steps 3000 --max-days 10"
        
        exit 0
    fi
    
    echo "Waiting for model to save... (${wait_time}s)"
    sleep 5
    wait_time=$((wait_time + 5))
done

echo "⚠ Model not found after ${max_wait} seconds"
echo "Checking for alternative models..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && find models -name '*.zip' -type f 2>/dev/null" || true

exit 1
