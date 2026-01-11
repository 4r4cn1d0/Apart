# Lambda Cloud Training Setup

This guide explains how to use the `lambda_cloud_trainer.py` script to run RL training on Lambda Cloud GPU instances.

## Quick Start

### 1. Install Dependencies

```powershell
pip install requests paramiko
```

### 2. Get Your Lambda Cloud API Token

1. Go to [Lambda Cloud Dashboard](https://cloud.lambdalabs.com)
2. Navigate to **API Keys** → **Create/View API Key**
3. Copy your API token (starts with `secret_...`)

**Option A: Environment Variable (Recommended for Security)**

```powershell
# PowerShell
$env:LAMBDA_CLOUD_API_TOKEN = "your_actual_api_token_here"

# Then run (token is automatically used)
python lambda_cloud_trainer.py --total-timesteps 1000000
```

**Option B: Command Line**

```powershell
python lambda_cloud_trainer.py --api-token "your_actual_api_token_here" --total-timesteps 1000000
```

### 3. Run Training

Basic usage:
```powershell
cd rl_env
python lambda_cloud_trainer.py --api-token "your_token" --total-timesteps 1000000 --n-envs 8
```

Full example with options:
```powershell
python lambda_cloud_trainer.py `
  --api-token "your_actual_api_token_here" `
  --instance-type gpu_1x_a10 `
  --region us-west-1 `
  --total-timesteps 2000000 `
  --n-envs 8 `
  --n-steps 2048 `
  --learning-rate 3e-4 `
  --ssh-private-key C:\Users\yasha\.ssh\lambda_key.pem
```

## What the Script Does

1. **Launches Lambda Cloud instance** - Creates a GPU instance
2. **Waits for instance to be ready** - Monitors status until active
3. **Establishes SSH connection** - Connects using your SSH key
4. **Transfers game files** - Uploads entire game directory via SCP
5. **Sets up environment** - Installs system packages and Python dependencies
6. **Runs training** - Executes training script (background or foreground)
7. **Downloads results** - Retrieves models, logs, and tensorboard data
8. **Terminates instance** - Stops instance to avoid charges (optional)

## Command-Line Options

### Required
- `--api-token`: Lambda Cloud API token (or set LAMBDA_CLOUD_API_TOKEN env var)

### Optional - Instance Configuration
- `--instance-type`: GPU type (default: `gpu_1x_a10`)
- `--region`: Region (default: `us-west-1`)
- `--ssh-key-name`: SSH key name in Lambda Cloud
- `--ssh-private-key`: Path to SSH private key file

### Optional - Training Parameters
- `--total-timesteps`: Total training timesteps (default: 1000000)
- `--n-envs`: Number of parallel environments (default: 8)
- `--learning-rate`: Learning rate (default: 3e-4)
- `--n-steps`: Steps per update (default: 2048)
- `--batch-size`: Batch size (default: 256)
- `--n-epochs`: Training epochs per update (default: 10)
- `--max-steps`: Max steps per episode (default: 10000)
- `--max-days`: Max days per episode (default: 30)

### Optional - Other
- `--local-game-path`: Local path to game directory (default: parent directory)
- `--results-dir`: Local directory for results (default: `./lambda_results`)
- `--no-background`: Run training in foreground (blocks until complete)
- `--no-terminate`: Don't terminate instance after completion
- `--skip-transfer`: Skip file transfer (files already on instance)
- `--skip-setup`: Skip environment setup (already set up)

## SSH Key Setup

The script needs an SSH private key to connect to the instance. Options:

1. **Provide via command line:**
   ```powershell
   --ssh-private-key C:\Users\yasha\.ssh\lambda_key.pem
   ```

2. **Use default locations** (script checks automatically):
   - `~/.ssh/id_rsa`
   - `~/.ssh/lambda_key`
   - `~/.ssh/lambda_key.pem`
   - `~/.ssh/id_ed25519`

3. **Add SSH key to Lambda Cloud** (then use `--ssh-key-name`)

## Monitoring Training

When training runs in background, you can monitor it:

```bash
# SSH into instance
ssh ubuntu@INSTANCE_IP

# View training logs
tail -f ~/game/training.log

# Check if training is still running
ps aux | grep train_ppo
```

## Downloading Results

Results are automatically downloaded when training completes, or manually:

```powershell
# The script will prompt to download, or you can SSH in and manually download
scp -r -i C:\Users\yasha\.ssh\lambda_key.pem ubuntu@INSTANCE_IP:~/game/rl_env/models ./models
scp -r -i C:\Users\yasha\.ssh\lambda_key.pem ubuntu@INSTANCE_IP:~/game/rl_env/tensorboard ./tensorboard
```

## Security Notes

⚠️ **Important**: Your API token is sensitive! 

- Don't commit it to git
- Use environment variables when possible
- Consider using a secrets manager for production
- The token shown here should be rotated if it's been exposed

## Troubleshooting

### "Permission denied (publickey)"
- Ensure you have the correct SSH private key
- Check key file permissions
- Verify key is added to Lambda Cloud (if using their key management)

### "Failed to launch instance"
- Check API token is correct
- Verify you have quota/credits in Lambda Cloud
- Check instance type availability in selected region

### File transfer fails
- Ensure SSH key is correct
- Check network connectivity
- Try transferring manually first to verify SSH works

### Training doesn't start
- SSH into instance and check logs: `cat ~/game/training.log`
- Verify environment setup completed successfully
- Check that all integration patches are applied

## Example Workflow

```powershell
# 1. Set API token
$env:LAMBDA_CLOUD_API_TOKEN = "your_actual_api_token_here"

# 2. Run training
cd rl_env
python lambda_cloud_trainer.py --total-timesteps 2000000 --n-envs 8

# Script will:
# - Launch instance
# - Transfer files
# - Setup environment
# - Start training (background)
# - Wait for completion (if you choose)
# - Download results
# - Terminate instance (if you choose)
```
