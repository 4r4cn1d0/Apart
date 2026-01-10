# Setting Up Inference Server on Lambda Labs Instance

## Step 1: SSH into Your Instance

```bash
ssh root@192.222.59.32
```

## Step 2: Install vLLM (Recommended for Vision Models)

Once you're SSH'd into the instance, run:

```bash
# Update system
apt-get update

# Install Python and pip if not already installed
apt-get install -y python3 python3-pip

# Install vLLM with vision support
pip3 install vllm[vision]

# Or if you prefer a specific version:
# pip3 install vllm==0.6.0
```

## Step 3: Start the Inference Server

For a vision-capable model like Llama 3.1 70B Vision:

```bash
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-70B-Vision-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code
```

**Note:** This will download the model (can be 40GB+), so it may take a while.

## Step 4: Test the Endpoint

In a new terminal (on your local machine), test:

```bash
curl http://192.222.59.32:8000/v1/models
```

If it works, you'll see a list of models.

## Step 5: Configure the Game

Once the server is running, update the game configuration:

```bash
export LAMBDA_API_KEY="secret_apart_58f182d70df5470086566cbd9ceccbc7.B7VkBa9N4KDNbxnNxxSt9uwHnx5FxSDY"
export LAMBDA_API_URL="http://192.222.59.32:8000"
export LAMBDA_MODEL="meta-llama/Llama-3.1-70B-Vision-Instruct"

python3 main.py --ai --api lambda
```

## Alternative: Using Text Generation Inference (TGI)

If vLLM doesn't work, try TGI:

```bash
# On the instance
docker run --gpus all -p 8000:80 \
    -v $PWD/data:/data \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id meta-llama/Llama-3.1-70B-Vision-Instruct \
    --port 80
```

## Troubleshooting

- **Port not accessible**: Check firewall rules in Lambda Labs dashboard
- **Model download fails**: Check disk space (`df -h`)
- **Out of memory**: Try a smaller model like `meta-llama/Llama-3.1-8B-Vision-Instruct`
