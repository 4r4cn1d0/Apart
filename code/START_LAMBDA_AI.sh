#!/bin/bash
# Start game with Lambda inference server

cd "/Users/spiderishi/Coding/AI Manipulation/code"

INSTANCE_IP="192.222.59.32"
ENDPOINT="http://$INSTANCE_IP:8000"

echo "=========================================="
echo "Lambda AI Game Controller"
echo "=========================================="
echo ""
echo "Lambda Instance: $INSTANCE_IP"
echo "Inference Endpoint: $ENDPOINT"
echo ""

# Check if server is running
echo "Checking inference server..."
health=$(curl -s --connect-timeout 3 "$ENDPOINT/health" 2>&1)

if echo "$health" | grep -q "ok\|loading"; then
    echo "✅ Inference server is running!"
    echo ""
else
    echo "⚠️  Inference server not responding"
    echo ""
    echo "Starting server on Lambda..."
    echo "(This may take 10-30 minutes on first run - model download)"
    echo ""
    
    ssh ubuntu@$INSTANCE_IP "cd /home/ubuntu && export PATH=\$HOME/.local/bin:\$PATH && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH && nohup python3 simple_inference_server.py > /tmp/inference.log 2>&1 &"
    
    echo "Server starting... (checking in 10 seconds)"
    sleep 10
    
    health=$(curl -s --connect-timeout 3 "$ENDPOINT/health" 2>&1)
    if echo "$health" | grep -q "ok\|loading"; then
        echo "✅ Server is now running!"
    else
        echo "⏳ Server is starting (model may be downloading)"
        echo "View progress: ssh ubuntu@$INSTANCE_IP 'tail -f /tmp/inference.log'"
    fi
    echo ""
fi

# Configure for Lambda
export LAMBDA_API_URL="$ENDPOINT"
export LAMBDA_MODEL="meta-llama/Meta-Llama-3.1-8B-Instruct"

echo "Configuration:"
echo "  Endpoint: $LAMBDA_API_URL"
echo "  Model: $LAMBDA_MODEL"
echo ""
echo "=========================================="
echo "Starting game..."
echo "All AI processing uses Lambda credits! 🚀"
echo "=========================================="
echo ""

python3 main.py --ai --api lambda
