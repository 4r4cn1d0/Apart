"""
Lambda Cloud Automation Script for SproutLand RL Training

Usage:
    python lambda_cloud_trainer.py --api-token YOUR_TOKEN [options]
    
Requirements:
    pip install requests paramiko
"""

import os
import sys
import time
import subprocess
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
    import paramiko
except ImportError:
    print("ERROR: Missing required packages. Install with:")
    print("pip install requests paramiko")
    sys.exit(1)

# Debug logging configuration
DEBUG_LOG_PATH = r"c:\Users\yasha\Documents\access-hack\game\.cursor\debug.log"

def debug_log(session_id: str, run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
    """Write debug log entry"""
    try:
        log_entry = {
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Fail silently to not break the script


class LambdaCloudTrainer:
    """Automated Lambda Cloud training manager"""
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        ssh_key_name: Optional[str] = None,
        ssh_private_key_path: Optional[str] = None
    ):
        """Initialize Lambda Cloud trainer"""
        self.api_token = api_token
        self.ssh_key_name = ssh_key_name
        self.ssh_private_key_path = ssh_private_key_path
        self.api_base = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}" if api_token else "",
            "Content-Type": "application/json"
        }
        self.instance_id = None
        self.instance_ip = None
        self.ssh_client = None
        self.sftp_client = None
    
    def validate_api_token(self) -> None:
        """Validate API token format and provide helpful error messages"""
        if not self.api_token:
            raise ValueError(
                "API token is required. Provide --api-token or set LAMBDA_CLOUD_API_TOKEN env var.\n"
                "Get your token from: https://cloud.lambdalabs.com → API Keys"
            )
        
        # Check for common placeholder values
        placeholder_values = ["your_token", "YOUR_TOKEN", "your_actual_api_token_here", ""]
        if self.api_token.strip() in placeholder_values:
            raise ValueError(
                f"ERROR: You used '{self.api_token}' which is a placeholder, not a real API token.\n\n"
                "To get your API token:\n"
                "1. Go to https://cloud.lambdalabs.com\n"
                "2. Navigate to API Keys → Create/View API Key\n"
                "3. Copy your token (it starts with 'secret_')\n"
                "4. Use it with: --api-token \"your_actual_token_here\"\n"
                "   Or set: $env:LAMBDA_CLOUD_API_TOKEN = \"your_actual_token_here\""
            )
        
        # Lambda Cloud tokens typically start with "secret_"
        if not self.api_token.startswith("secret_"):
            print(
                "⚠ WARNING: API token doesn't start with 'secret_'. "
                "Lambda Cloud tokens usually start with 'secret_'.\n"
                "Make sure you copied the full token from the dashboard."
            )
    
    def get_ssh_keys(self) -> list:
        """Fetch SSH keys from Lambda Cloud account"""
        try:
            response = requests.get(
                f"{self.api_base}/ssh-keys",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return [key["name"] for key in data["data"]]
            return []
        except Exception:
            return []
    
    def launch_instance(self, instance_type: str = "gpu_1x_gh200", region: str = "us-east-3") -> None:
        """Launch a Lambda Cloud instance"""
        # #region agent log
        debug_log("debug-session", "post-fix", "A", "lambda_cloud_trainer.py:101", "launch_instance entry", {
            "instance_type": instance_type,
            "region": region,
            "api_base": self.api_base,
            "has_ssh_key_name": bool(self.ssh_key_name)
        })
        # #endregion
        
        # Validate token first
        self.validate_api_token()
        
        print(f"\n{'='*60}")
        print(f"Launching {instance_type} instance in {region}...")
        print(f"{'='*60}")
        
        # Prepare SSH keys - Lambda Cloud API requires exactly one SSH key name
        ssh_key_name = self.ssh_key_name
        
        # If no SSH key name provided, try to fetch and use the first one
        if not ssh_key_name:
            print("No SSH key name provided. Fetching SSH keys from your account...")
            ssh_keys = self.get_ssh_keys()
            # #region agent log
            debug_log("debug-session", "post-fix", "A", "lambda_cloud_trainer.py:129", "fetched SSH keys", {
                "ssh_keys_count": len(ssh_keys),
                "ssh_keys": ssh_keys[:3] if ssh_keys else []
            })
            # #endregion
            
            if ssh_keys:
                ssh_key_name = ssh_keys[0]
                print(f"Using first SSH key: {ssh_key_name}")
            else:
                raise ValueError(
                    "SSH key name is required but not provided.\n\n"
                    "Lambda Cloud API requires exactly one SSH key name to launch an instance.\n\n"
                    "To fix this:\n"
                    "1. Add an SSH key to Lambda Cloud:\n"
                    "   - Go to https://cloud.lambdalabs.com → SSH Keys\n"
                    "   - Click 'Add SSH Key'\n"
                    "   - Paste your public key (from ~/.ssh/id_rsa.pub or similar)\n"
                    "2. Then use: --ssh-key-name \"YourKeyName\"\n\n"
                    "Or provide --ssh-key-name with the name of an existing SSH key in your account."
                )
        
        ssh_key_names = [ssh_key_name]
        
        payload = {
            "instance_type_name": instance_type,
            "region_name": region,
            "ssh_key_names": ssh_key_names,
            "quantity": 1
        }
        
        # #region agent log
        debug_log("debug-session", "post-fix", "A", "lambda_cloud_trainer.py:174", "payload before request", {
            "payload": payload,
            "api_endpoint": f"{self.api_base}/instance-operations/launch",
            "ssh_key_name_used": ssh_key_name
        })
        # #endregion
        
        try:
            response = requests.post(
                f"{self.api_base}/instance-operations/launch",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # #region agent log
            debug_log("debug-session", "post-fix", "A", "lambda_cloud_trainer.py:165", "response received", {
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "response_body": response.text[:500] if response.text else None
            })
            # #endregion
            
            # Handle 401 Unauthorized with helpful error message
            if response.status_code == 401:
                # #region agent log
                debug_log("debug-session", "run1", "B", "lambda_cloud_trainer.py:113", "401 error detected", {
                    "response_body": response.text[:500] if response.text else None
                })
                # #endregion
                raise Exception(
                    "401 Unauthorized: Invalid API token.\n\n"
                    "This means your API token is incorrect or invalid.\n\n"
                    "To fix this:\n"
                    "1. Go to https://cloud.lambdalabs.com → API Keys\n"
                    "2. Create a new API key or copy your existing one\n"
                    "3. Make sure you're using the full token (starts with 'secret_')\n"
                    "4. Don't use placeholder values like 'your_token'\n\n"
                    f"You provided: '{self.api_token[:20]}...' (truncated for security)"
                )
            
            # Handle 400 Bad Request with detailed error message
            if response.status_code == 400:
                # #region agent log
                debug_log("debug-session", "run1", "C", "lambda_cloud_trainer.py:130", "400 error detected", {
                    "response_body": response.text[:1000] if response.text else None,
                    "payload_sent": payload
                })
                # #endregion
                try:
                    error_data = response.json()
                    error_msg = json.dumps(error_data, indent=2)
                except:
                    error_msg = response.text[:500] if response.text else "No error details available"
                
                raise Exception(
                    f"400 Bad Request: Invalid parameters.\n\n"
                    f"API Error Details:\n{error_msg}\n\n"
                    f"Payload sent: {json.dumps(payload, indent=2)}\n\n"
                    f"Common causes:\n"
                    f"1. Invalid instance type: '{instance_type}'\n"
                    f"2. Invalid region: '{region}'\n"
                    f"3. SSH key name not found in your account\n"
                    f"4. Missing required fields\n\n"
                    f"Check Lambda Cloud dashboard for valid instance types and regions."
                )
            
            response.raise_for_status()
            
            data = response.json()
            if "data" not in data or "instance_ids" not in data["data"]:
                raise Exception(f"Unexpected API response: {data}")
            
            self.instance_id = data["data"]["instance_ids"][0]
            print(f"✓ Instance launched: {self.instance_id}")
            
        except requests.exceptions.RequestException as e:
            if "401" in str(e):
                raise Exception(
                    "401 Unauthorized: Invalid API token.\n\n"
                    "Your API token is incorrect or invalid.\n"
                    "Get a valid token from: https://cloud.lambdalabs.com → API Keys"
                ) from e
            raise Exception(f"Failed to launch instance: {e}")
        
        # Wait for instance to be ready
        self.wait_for_instance()
    
    def wait_for_instance(self, max_wait: int = 1200) -> None:
        """Wait for instance to be ready and get IP address"""
        print(f"\nWaiting for instance to be ready (max {max_wait}s)...")
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.api_base}/instances",
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 401:
                    raise Exception("401 Unauthorized: API token is invalid")
                
                response.raise_for_status()
                
                instances = response.json()["data"]
                instance = next((i for i in instances if i["id"] == self.instance_id), None)
                
                if not instance:
                    time.sleep(5)
                    continue
                
                status = instance.get("status", "unknown")
                if status != last_status:
                    print(f"  Instance status: {status}")
                    last_status = status
                
                if status == "active" and instance.get("ip"):
                    self.instance_ip = instance["ip"]
                    print(f"✓ Instance ready! IP: {self.instance_ip}")
                    return
                
            except requests.exceptions.RequestException as e:
                print(f"  Warning: Error checking status: {e}")
            
            time.sleep(5)
        
        raise Exception(f"Instance did not become ready within {max_wait} seconds")
    
    def setup_ssh(self) -> None:
        """Setup SSH connection to instance"""
        print(f"\n{'='*60}")
        print("Setting up SSH connection...")
        print(f"{'='*60}")
        
        if not self.instance_ip:
            raise Exception("Instance IP not available. Launch instance first.")
        
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Try to connect with provided key
        key = None
        if self.ssh_private_key_path:
            if not os.path.exists(self.ssh_private_key_path):
                raise Exception(f"Private key file not found: {self.ssh_private_key_path}")
            
            try:
                key = paramiko.RSAKey.from_private_key_file(self.ssh_private_key_path)
            except Exception as e:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(self.ssh_private_key_path)
                except Exception:
                    raise Exception(f"Failed to load private key: {e}")
        
        # Try default key locations if not provided
        if not key:
            default_key_paths = [
                os.path.expanduser("~/.ssh/id_rsa"),
                os.path.expanduser("~/.ssh/lambda_key"),
                os.path.expanduser("~/.ssh/lambda_key.pem"),
                os.path.expanduser("~/.ssh/id_ed25519"),
            ]
            
            for key_path in default_key_paths:
                if os.path.exists(key_path):
                    try:
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                        print(f"Using default key: {key_path}")
                        break
                    except:
                        try:
                            key = paramiko.Ed25519Key.from_private_key_file(key_path)
                            print(f"Using default key: {key_path}")
                            break
                        except:
                            continue
        
        if not key:
            raise Exception(
                "No SSH private key found. Please provide --ssh-private-key or "
                "place key in ~/.ssh/id_rsa or ~/.ssh/lambda_key"
            )
        
        # Connect
        max_retries = 5
        last_error = None
        for attempt in range(max_retries):
            try:
                self.ssh_client.connect(
                    hostname=self.instance_ip,
                    username="ubuntu",
                    pkey=key,
                    timeout=30,
                    look_for_keys=False
                )
                print("✓ SSH connection established!")
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"  Connection attempt {attempt + 1} failed, retrying in 5s...")
                    time.sleep(5)
                else:
                    # Provide helpful error message for authentication failures
                    error_str = str(e)
                    if "Authentication failed" in error_str or "AuthenticationException" in error_str:
                        ssh_key_name_used = self.ssh_key_name or "Yash"  # Default to first key if auto-selected
                        key_file_used = self.ssh_private_key_path or "default key (~/.ssh/id_rsa)"
                        raise Exception(
                            f"SSH Authentication failed.\n\n"
                            f"Lambda Cloud SSH key name used: '{ssh_key_name_used}'\n"
                            f"Private key file tried: {key_file_used}\n\n"
                            f"The private key file you're using doesn't match the public key '{ssh_key_name_used}' "
                            f"that was uploaded to Lambda Cloud.\n\n"
                            f"To fix this:\n"
                            f"1. Find the private key file that corresponds to the public key '{ssh_key_name_used}' "
                            f"you uploaded to Lambda Cloud\n"
                            f"2. Use: --ssh-private-key \"path/to/your/private/key\"\n\n"
                            f"If you don't have the private key:\n"
                            f"- You'll need to generate a new SSH key pair\n"
                            f"- Add the public key to Lambda Cloud (Dashboard → SSH Keys)\n"
                            f"- Use the private key file with --ssh-private-key\n\n"
                            f"Original error: {error_str}"
                        )
                    raise Exception(f"Failed to establish SSH connection: {e}")
    
    def run_command(self, command: str, timeout: int = 300, check: bool = True) -> tuple:
        """Run command on remote instance"""
        stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if check and exit_status != 0:
            raise Exception(f"Command failed (exit {exit_status}): {command}\nError: {error}")
        
        return exit_status, output, error
    
    def transfer_files(self, local_path: str, remote_path: str = "~/game") -> None:
        """Transfer game directory to instance using scp"""
        print(f"\n{'='*60}")
        print(f"Transferring files from {local_path} to {remote_path}...")
        print(f"{'='*60}")
        
        local_path = os.path.abspath(local_path)
        if not os.path.exists(local_path):
            raise Exception(f"Local path does not exist: {local_path}")
        
        # Determine key path for scp
        key_path = self.ssh_private_key_path
        if not key_path:
            for default_path in [os.path.expanduser("~/.ssh/id_rsa"),
                                os.path.expanduser("~/.ssh/lambda_key"),
                                os.path.expanduser("~/.ssh/lambda_key.pem")]:
                if os.path.exists(default_path):
                    key_path = default_path
                    break
        
        if not key_path:
            raise Exception("No SSH key found for file transfer")
        
        # Build scp command
        scp_command = [
            "scp",
            "-r",
            "-i", key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-C",
            local_path,
            f"ubuntu@{self.instance_ip}:{remote_path}"
        ]
        
        print(f"Running: scp -r -i {key_path} ... {remote_path}")
        result = subprocess.run(scp_command, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            print(f"SCP stderr: {result.stderr}")
            raise Exception(f"File transfer failed (exit {result.returncode}): {result.stderr}")
        
        print("✓ Files transferred successfully!")
    
    def setup_environment(self) -> None:
        """Setup Python environment on instance"""
        print(f"\n{'='*60}")
        print("Setting up environment on instance...")
        print(f"{'='*60}")
        
        commands = [
            ("sudo apt update", 120),
            ("sudo apt install -y python3 python3-pip python3-venv python3-dev "
             "libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev "
             "libpng-dev libjpeg-dev libfreetype6-dev libx11-dev libffi-dev", 300),
            ("cd ~/game && python3 -m venv venv", 60),
            ("cd ~/game && source venv/bin/activate && "
             "pip install --upgrade pip && "
             "pip install gymnasium stable-baselines3[extra] 'numpy<2.0,>=1.22' pygame pytmx tensorboard", 600)
        ]
        
        for cmd, timeout in commands:
            print(f"\nRunning: {cmd[:80]}...")
            try:
                exit_status, output, error = self.run_command(cmd, timeout=timeout, check=False)
                if exit_status != 0:
                    print(f"Warning: Command had non-zero exit ({exit_status})")
                    if error:
                        print(f"Error output: {error[:200]}")
                else:
                    print("✓ Command completed successfully")
            except Exception as e:
                print(f"Error running command: {e}")
                raise
        
        print("\n✓ Environment setup complete!")
    
    def run_training(self, training_args: Dict[str, Any], run_in_background: bool = True) -> None:
        """Run training on instance"""
        print(f"\n{'='*60}")
        print("Starting training...")
        print(f"{'='*60}")
        
        train_cmd_parts = ["cd ~/game/rl_env", "source ~/game/venv/bin/activate", "python train_ppo.py"]
        
        for key, value in training_args.items():
            if value is not None:
                arg_name = key.replace('_', '-')
                train_cmd_parts.append(f"--{arg_name} {value}")
        
        train_cmd = " && ".join(train_cmd_parts)
        
        print(f"Training command:")
        print(f"  {train_cmd[:100]}...")
        
        if run_in_background:
            bg_cmd = f"nohup bash -c '{train_cmd}' > ~/game/training.log 2>&1 & echo $!"
            exit_status, output, error = self.run_command(bg_cmd, timeout=60)
            pid = output.strip()
            print(f"\n✓ Training started in background (PID: {pid})")
            print(f"\nMonitor training:")
            print(f"  ssh ubuntu@{self.instance_ip} 'tail -f ~/game/training.log'")
        else:
            print("\nRunning training in foreground (this will take a while)...")
            self.run_command(train_cmd, timeout=None, check=False)
    
    def download_results(self, local_dest: str = "./lambda_results") -> None:
        """Download training results from instance"""
        print(f"\n{'='*60}")
        print(f"Downloading results to {local_dest}...")
        print(f"{'='*60}")
        
        os.makedirs(local_dest, exist_ok=True)
        
        key_path = self.ssh_private_key_path
        if not key_path:
            for default_path in [os.path.expanduser("~/.ssh/id_rsa"),
                                os.path.expanduser("~/.ssh/lambda_key"),
                                os.path.expanduser("~/.ssh/lambda_key.pem")]:
                if os.path.exists(default_path):
                    key_path = default_path
                    break
        
        if not key_path:
            raise Exception("No SSH key found for file download")
        
        downloads = [
            ("~/game/rl_env/models", f"{local_dest}/models"),
            ("~/game/rl_env/tensorboard", f"{local_dest}/tensorboard"),
            ("~/game/training.log", f"{local_dest}/training.log"),
        ]
        
        scp_base = [
            "scp", "-r", "-i", key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-C"
        ]
        
        for remote_path, local_path in downloads:
            print(f"\nDownloading: {remote_path} -> {local_path}")
            scp_cmd = scp_base + [f"ubuntu@{self.instance_ip}:{remote_path}", local_path]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✓ Downloaded: {local_path}")
            else:
                print(f"⚠ Warning: Failed to download {remote_path}")
                print(f"  Error: {result.stderr[:200]}")
        
        print(f"\n✓ Results downloaded to {local_dest}")
    
    def terminate_instance(self) -> None:
        """Terminate the Lambda Cloud instance"""
        if not self.instance_id:
            print("No instance to terminate")
            return
        
        print(f"\n{'='*60}")
        print(f"Terminating instance {self.instance_id}...")
        print(f"{'='*60}")
        
        try:
            response = requests.post(
                f"{self.api_base}/instance-operations/terminate",
                headers=self.headers,
                json={"instance_ids": [self.instance_id]},
                timeout=30
            )
            response.raise_for_status()
            print("✓ Instance terminated successfully")
        except Exception as e:
            print(f"⚠ Warning: Failed to terminate instance: {e}")
    
    def cleanup(self) -> None:
        """Cleanup SSH connections"""
        if self.sftp_client:
            try:
                self.sftp_client.close()
            except:
                pass
        
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Automated Lambda Cloud training for SproutLand RL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Using environment variable (recommended):
  $env:LAMBDA_CLOUD_API_TOKEN = "your_token"
  python lambda_cloud_trainer.py --total-timesteps 1000000
  
  # Using command line:
  python lambda_cloud_trainer.py --api-token YOUR_TOKEN --total-timesteps 1000000
  
Get your API token from: https://cloud.lambdalabs.com → API Keys
        """
    )
    
    default_api_token = os.environ.get("LAMBDA_CLOUD_API_TOKEN")
    parser.add_argument("--api-token", type=str, default=default_api_token,
                       help="Lambda Cloud API token (or set LAMBDA_CLOUD_API_TOKEN env var)")
    parser.add_argument("--ssh-key-name", type=str, default=None,
                       help="SSH key name in Lambda Cloud")
    parser.add_argument("--ssh-private-key", type=str, default=None,
                       help="Path to SSH private key file")
    parser.add_argument("--instance-type", type=str, default="gpu_1x_gh200",
                       help="Lambda Cloud instance type (default: gpu_1x_a10)")
    parser.add_argument("--region", type=str, default="us-east-3",
                       help="Lambda Cloud region (default: us-west-1)")
    parser.add_argument("--local-game-path", type=str,
                       default=os.path.join(os.path.dirname(__file__), ".."),
                       help="Local path to game directory")
    parser.add_argument("--results-dir", type=str, default="./lambda_results",
                       help="Local directory for results")
    parser.add_argument("--total-timesteps", type=int, default=1_000_000,
                       help="Total training timesteps")
    parser.add_argument("--n-envs", type=int, default=8,
                       help="Number of parallel environments")
    parser.add_argument("--learning-rate", type=float, default=3e-4,
                       help="Learning rate")
    parser.add_argument("--n-steps", type=int, default=2048,
                       help="Steps per update")
    parser.add_argument("--batch-size", type=int, default=256,
                       help="Batch size")
    parser.add_argument("--n-epochs", type=int, default=10,
                       help="Training epochs per update")
    parser.add_argument("--max-steps", type=int, default=10000,
                       help="Max steps per episode")
    parser.add_argument("--max-days", type=int, default=30,
                       help="Max days per episode")
    parser.add_argument("--no-background", action="store_true",
                       help="Run training in foreground")
    parser.add_argument("--no-terminate", action="store_true",
                       help="Don't terminate instance after completion")
    parser.add_argument("--skip-transfer", action="store_true",
                       help="Skip file transfer")
    parser.add_argument("--skip-setup", action="store_true",
                       help="Skip environment setup")
    
    args = parser.parse_args()
    
    local_game_path = os.path.abspath(args.local_game_path)
    
    training_args = {
        "total_timesteps": args.total_timesteps,
        "n_envs": args.n_envs,
        "learning_rate": args.learning_rate,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "n_epochs": args.n_epochs,
        "max_steps": args.max_steps,
        "max_days": args.max_days,
        "tensorboard_log": "./tensorboard",
        "save_dir": "./models",
        "log_dir": "./logs",
    }
    
    trainer = LambdaCloudTrainer(
        api_token=args.api_token,
        ssh_key_name=args.ssh_key_name,
        ssh_private_key_path=args.ssh_private_key
    )
    
    try:
        trainer.launch_instance(args.instance_type, args.region)
        trainer.setup_ssh()
        
        if not args.skip_transfer:
            trainer.transfer_files(local_game_path)
        
        if not args.skip_setup:
            trainer.setup_environment()
        
        trainer.run_training(training_args, run_in_background=not args.no_background)
        
        if args.no_background:
            trainer.download_results(args.results_dir)
        else:
            print(f"\n{'='*60}")
            print("Training is running in background!")
            print(f"{'='*60}")
            print(f"\nInstance IP: {trainer.instance_ip}")
            print(f"\nMonitor: ssh ubuntu@{trainer.instance_ip} 'tail -f ~/game/training.log'")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        trainer.cleanup()
        
        if not args.no_terminate and trainer.instance_id:
            response = input("\nTerminate instance? (yes/no): ").strip().lower()
            if response == "yes":
                trainer.terminate_instance()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
