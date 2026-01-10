#!/bin/bash
# Script to run on your Lambda Labs instance via SSH
# Copy and paste these commands after SSH'ing into your instance

echo "=========================================="
echo "Lambda Labs Inference Server Setup"
echo "=========================================="
echo ""

# Update system
echo "Step 1: Updating system..."
apt-get update -y

# Install dependencies
echo "Step 2: Installing dependencies..."
apt-get install -y python3 python3-pip git

# Install vLLM with vision support
echo "Step 3: Installing vLLM (this may take a few minutes)..."
pip3 install vllm[vision] --break-system-packages

# Create a startup script
echo "Step 4: Creating startup script..."
cat > /root/start_inference.sh << 'EOF'
#!/bin/bash
# Start vLLM inference server

MODEL="meta-llama/Llama-3.1-70B-Vision-Instruct"
# For smaller/faster model, use:
# MODEL="meta-llama/Llama-3.1-8B-Vision-Instruct"

echo "Starting inference server with model: $MODEL"
echo "This will download the model on first run (may take 10-30 minutes)"
echo ""

python3 -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code \
    --max-model-len 8192
EOF

chmod +x /root/start_inference.sh

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the inference server, run:"
echo "  /root/start_inference.sh"
echo ""
echo "Or start it in the background:"
echo "  nohup /root/start_inference.sh > /root/inference.log 2>&1 &"
echo ""
echo "To check if it's running:"
echo "  curl http://localhost:8000/v1/models"
echo ""
echo "To view logs:"
echo "  tail -f /root/inference.log"
echo ""
