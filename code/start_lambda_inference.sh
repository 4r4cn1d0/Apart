#!/bin/bash
# Start inference server on Lambda instance in background

INSTANCE_IP="192.222.59.32"

echo "Starting inference server on Lambda instance..."
echo "This may take 10-30 minutes on first run (model download)"
echo ""

ssh ubuntu@$INSTANCE_IP "export PATH=\$HOME/.local/bin:\$PATH && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH && nohup /home/ubuntu/start_inference.sh > /tmp/inference.log 2>&1 &"

echo "Server starting in background..."
echo "Check status with: ssh ubuntu@$INSTANCE_IP 'tail -f /tmp/inference.log'"
echo ""
echo "Once ready, test with:"
echo "  curl http://$INSTANCE_IP:8000/v1/models"
