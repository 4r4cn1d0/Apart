#!/bin/bash
# Setup inference server on Lambda instance
# This runs ON the Lambda instance

INSTANCE_IP="192.222.59.32"

echo "=========================================="
echo "Setting up Lambda Inference Server"
echo "=========================================="
echo ""
echo "This will:"
echo "  1. Install/check vLLM on Lambda instance"
echo "  2. Start inference server on port 8000"
echo "  3. Configure game to use Lambda endpoint"
echo ""

# Check if vLLM is installed
echo "Checking vLLM installation..."
ssh ubuntu@$INSTANCE_IP "export PATH=\$HOME/.local/bin:\$PATH && python3 -c 'import vllm; print(\"vLLM version:\", vllm.__version__)' 2>&1" | head -5

echo ""
echo "Starting inference server on Lambda..."
echo "This will download the model on first run (10-30 minutes)"
echo ""

# Create startup script on Lambda
ssh ubuntu@$INSTANCE_IP "cat > /home/ubuntu/start_inference.sh << 'EOFSCRIPT'
#!/bin/bash
export PATH=\$HOME/.local/bin:\$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH

# Use 8B model for faster startup (change to 70B for better quality)
MODEL=\"meta-llama/Llama-3.1-8B-Vision-Instruct\"

echo \"Starting inference server with model: \$MODEL\"
echo \"Endpoint will be: http://$INSTANCE_IP:8000\"
echo \"\"

python3 -m vllm.entrypoints.openai.api_server \\
    --model \$MODEL \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --trust-remote-code \\
    --max-model-len 8192
EOFSCRIPT
chmod +x /home/ubuntu/start_inference.sh && echo 'Startup script created'"

echo ""
echo "To start the server, SSH into Lambda and run:"
echo "  ssh ubuntu@$INSTANCE_IP"
echo "  screen -S inference"
echo "  /home/ubuntu/start_inference.sh"
echo "  (Press Ctrl+A then D to detach)"
echo ""
echo "Or start it in background:"
echo "  ssh ubuntu@$INSTANCE_IP 'nohup /home/ubuntu/start_inference.sh > /tmp/inference.log 2>&1 &'"
echo ""
echo "Once running, configure game with:"
echo "  export LAMBDA_API_URL=\"http://$INSTANCE_IP:8000\""
echo "  export LAMBDA_MODEL=\"meta-llama/Llama-3.1-8B-Vision-Instruct\""
echo "  python3 main.py --ai --api lambda"
echo ""
