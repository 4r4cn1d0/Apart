#!/bin/bash
# Wait for training to complete, then evaluate model with rendering

SSH_KEY="$HOME/.ssh/id_ed25519"
HOST="ubuntu@209.20.157.218"
REMOTE_DIR="~/game/rl_env"
FINAL_MODEL="models/ppo_sproutland_final.zip"

echo "========================================="
echo "  Waiting for Training to Complete"
echo "========================================="
echo ""

# Check every 30 seconds for model
while true; do
    # Check if model exists
    if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && test -f $FINAL_MODEL"; then
        echo ""
        echo "✓ Model found! Starting evaluation with rendering..."
        echo ""
        
        # Run evaluation
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && \
            source ~/game/venv/bin/activate && \
            export PYTHONPATH=\$HOME/game/code:\$PYTHONPATH && \
            python evaluate.py $FINAL_MODEL --single --render --max-steps 3000 --max-days 10"
        
        exit 0
    fi
    
    # Check training status
    if ! ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd $REMOTE_DIR && ps aux | grep -E 'python.*train_ppo' | grep -v grep > /dev/null"; then
        echo "Training appears to have completed, waiting for model to save..."
        sleep 10
        continue
    fi
    
    # Still training
    echo -n "."
    sleep 30
done
