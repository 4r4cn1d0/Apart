# Final Lambda Setup - Working Solution

## Status
✅ Lambda instance running  
✅ PyTorch with CUDA working  
✅ Dependencies installed  
⚠️ Need to start inference server  

## Quick Start

### 1. Start Inference Server on Lambda

SSH into Lambda and run:

```bash
ssh ubuntu@192.222.59.32

# Start server in screen (stays running after disconnect)
screen -S inference
export PATH=$HOME/.local/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
cd /home/ubuntu
python3 simple_inference_server.py

# Press Ctrl+A then D to detach
```

### 2. Run Game (Local, uses Lambda for AI)

```bash
cd "/Users/spiderishi/Coding/AI Manipulation/code"
export LAMBDA_API_URL="http://192.222.59.32:8000"
export LAMBDA_MODEL="meta-llama/Meta-Llama-3.1-8B-Instruct"
python3 main.py --ai --api lambda
```

## Architecture

```
Your Mac                    Lambda Instance (192.222.59.32)
┌──────────┐               ┌──────────────────────────┐
│  Game    │  HTTP ──────> │  Inference Server :8000   │
│ (Local)  │  <── JSON ─── │  (Transformers + PyTorch) │
└──────────┘               └──────────────────────────┘
     │                              │
     │ Screenshots                  │ AI Decisions
     └──────────────────────────────┘
```

**All AI processing happens on Lambda - using your credits!** 🎯

## Troubleshooting

**Server won't start:**
- Check logs: `ssh ubuntu@192.222.59.32 'tail -f /tmp/inference.log'`
- Check GPU: `ssh ubuntu@192.222.59.32 'nvidia-smi'`

**Can't connect:**
- Check firewall: Allow TCP port 8000 in Lambda dashboard
- Test: `curl http://192.222.59.32:8000/health`

**Model download:**
- First run downloads model (~15GB, 10-30 min)
- Subsequent runs are instant
