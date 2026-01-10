# Quick Setup Guide for Lambda Labs + AI Game

## What You Have
- ✅ Lambda Labs instance running (IP: 192.222.59.32)
- ✅ API key
- ✅ SSH key configured

## What You Need to Do

### Option A: Automated Setup (Recommended)

1. **SSH into your instance:**
   ```bash
   ssh root@192.222.59.32
   ```

2. **Copy and run the setup script:**
   ```bash
   # On the instance, run:
   bash <(curl -s https://raw.githubusercontent.com/vllm-project/vllm/main/scripts/install.sh)
   # Or manually install:
   pip3 install vllm[vision] --break-system-packages
   ```

3. **Start the inference server:**
   ```bash
   python3 -m vllm.entrypoints.openai.api_server \
       --model meta-llama/Llama-3.1-70B-Vision-Instruct \
       --host 0.0.0.0 \
       --port 8000 \
       --trust-remote-code
   ```
   
   **Note:** First run will download the model (~40GB), takes 10-30 minutes.

4. **Keep it running** (in a screen/tmux session):
   ```bash
   # Install screen
   apt-get install -y screen
   
   # Start screen session
   screen -S inference
   
   # Run the server (inside screen)
   python3 -m vllm.entrypoints.openai.api_server \
       --model meta-llama/Llama-3.1-70B-Vision-Instruct \
       --host 0.0.0.0 \
       --port 8000 \
       --trust-remote-code
   
   # Press Ctrl+A then D to detach
   # Reattach later with: screen -r inference
   ```

### Option B: Use a Smaller/Faster Model

If 70B is too slow or uses too much memory:

```bash
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Vision-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code
```

## Test the Server

From your local machine (new terminal):

```bash
curl http://192.222.59.32:8000/v1/models
```

Should return JSON with model info.

## Run the Game

Once the server is running:

```bash
cd "/Users/spiderishi/Coding/AI Manipulation/code"

export LAMBDA_API_KEY="secret_apart_58f182d70df5470086566cbd9ceccbc7.B7VkBa9N4KDNbxnNxxSt9uwHnx5FxSDY"
export LAMBDA_API_URL="http://192.222.59.32:8000"
export LAMBDA_MODEL="meta-llama/Llama-3.1-70B-Vision-Instruct"

python3 main.py --ai --api lambda
```

## Troubleshooting

**Can't connect to port 8000:**
- Check Lambda Labs dashboard → Firewall rules
- Add rule: Allow TCP port 8000 from your IP

**Model download fails:**
- Check disk space: `df -h` (need ~50GB free)
- Check internet connection on instance

**Out of memory:**
- Use smaller model (8B instead of 70B)
- Or use a larger instance type

**Server stops when you disconnect:**
- Use `screen` or `tmux` to keep it running
- Or use `nohup`:
  ```bash
  nohup python3 -m vllm.entrypoints.openai.api_server ... > server.log 2>&1 &
  ```
