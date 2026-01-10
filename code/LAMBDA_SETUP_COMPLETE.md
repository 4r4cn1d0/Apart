# ✅ Lambda Instance Setup Complete!

## What's Configured

✅ **Lambda Instance**: 192.222.59.32  
✅ **vLLM**: Installed and working  
✅ **Inference Server**: Startup script ready  
✅ **Game Configuration**: Set to use Lambda endpoint  

## How to Use

### Start the Inference Server on Lambda

**Option 1: Background (Recommended)**
```bash
ssh ubuntu@192.222.59.32
nohup /home/ubuntu/start_inference.sh > /tmp/inference.log 2>&1 &
```

**Option 2: In Screen (Keeps running after disconnect)**
```bash
ssh ubuntu@192.222.59.32
screen -S inference
/home/ubuntu/start_inference.sh
# Press Ctrl+A then D to detach
```

**Option 3: Use the automated script**
```bash
cd "/Users/spiderishi/Coding/AI Manipulation/code"
./START_WITH_LAMBDA.sh
```

### Run the Game (Local, but uses Lambda for AI)

```bash
cd "/Users/spiderishi/Coding/AI Manipulation/code"
./START_WITH_LAMBDA.sh
```

Or manually:
```bash
export LAMBDA_API_URL="http://192.222.59.32:8000"
export LAMBDA_MODEL="meta-llama/Llama-3.1-8B-Vision-Instruct"
python3 main.py --ai --api lambda
```

## Check Server Status

```bash
# Check if running
curl http://192.222.59.32:8000/v1/models

# View logs
ssh ubuntu@192.222.59.32 'tail -f /tmp/inference.log'

# Check process
ssh ubuntu@192.222.59.32 'ps aux | grep api_server'
```

## First Run Notes

- **First time**: Model download takes 10-30 minutes (~15GB for 8B model)
- **Subsequent runs**: Starts in ~1-2 minutes
- **Game will wait**: If server isn't ready, game will retry

## Architecture

```
Your Mac (Local)                    Lambda Instance
┌─────────────┐                     ┌──────────────┐
│   Game      │  ────HTTP──────>    │  Inference  │
│  (Pygame)   │  <───JSON───────    │   Server    │
│             │                     │  (vLLM)     │
└─────────────┘                     └──────────────┘
     │                                      │
     │                                      │
     └──────────> Screenshots ─────────────┘
                  AI Decisions <────────────┘
```

**Everything AI-related goes through Lambda!** 🚀
