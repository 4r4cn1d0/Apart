#!/bin/bash
# Start game with Lambda instance inference server

cd "/Users/spiderishi/Coding/AI Manipulation/code"

INSTANCE_IP="192.222.59.32"
INSTANCE_ENDPOINT="http://$INSTANCE_IP:8000"

echo "=========================================="
echo "Starting Game with Lambda Inference"
echo "=========================================="
echo ""
echo "Lambda Instance: $INSTANCE_IP"
echo "Inference Endpoint: $INSTANCE_ENDPOINT"
echo ""

# Check if inference server is running
echo "Checking if inference server is running..."
response=$(curl -s --connect-timeout 3 "$INSTANCE_ENDPOINT/v1/models" 2>&1)

if echo "$response" | grep -q "model"; then
    echo "✅ Inference server is running!"
    echo ""
else
    echo "❌ Inference server not running on port 8000"
    echo ""
    echo "Starting inference server on Lambda..."
    echo "(This may take 10-30 minutes on first run)"
    echo ""
    
    # Start server in background
    ssh ubuntu@$INSTANCE_IP "export PATH=\$HOME/.local/bin:\$PATH && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH && nohup /home/ubuntu/start_inference.sh > /tmp/inference.log 2>&1 &"
    
    echo "Server starting... Waiting 10 seconds..."
    sleep 10
    
    # Check again
    response=$(curl -s --connect-timeout 3 "$INSTANCE_ENDPOINT/v1/models" 2>&1)
    if echo "$response" | grep -q "model"; then
        echo "✅ Server is now running!"
    else
        echo "⏳ Server is starting (model may be downloading)"
        echo "Check status: ssh ubuntu@$INSTANCE_IP 'tail -f /tmp/inference.log'"
        echo ""
        echo "You can start the game anyway - it will wait for the server"
    fi
    echo ""
fi

# Configure for Lambda
export LAMBDA_API_URL="$INSTANCE_ENDPOINT"
export LAMBDA_MODEL="meta-llama/Llama-3.1-8B-Vision-Instruct"
# API key not needed for direct instance endpoint
export LAMBDA_API_KEY="not-needed"

echo "Configuration:"
echo "  Endpoint: $LAMBDA_API_URL"
echo "  Model: $LAMBDA_MODEL"
echo ""
echo "Starting game..."
echo ""

python3 main.py --ai --api lambda
