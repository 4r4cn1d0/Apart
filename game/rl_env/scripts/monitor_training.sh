#!/bin/bash
# Real-time training monitor - displays key metrics continuously

SSH_KEY="$HOME/.ssh/id_ed25519"
HOST="ubuntu@209.20.157.218"
LOG_FILE="~/game/rl_env/training_h100_8x.log"

echo "Training Monitor - Press Ctrl+C to stop"
echo "========================================"
echo ""

while true; do
    # Clear screen and show header
    clear
    echo "════════════════════════════════════════════════════════════════"
    echo "  Real-Time Training Monitor - 8x H100 Instance"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    # Get training metrics
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" "cd ~/game/rl_env && python3 << 'PYEOF'
import re
import sys
from datetime import datetime

try:
    with open('training_h100_8x.log', 'r') as f:
        lines = f.readlines()
    
    # Extract metrics
    iterations = []
    rewards = []
    timesteps = []
    explained_vars = []
    losses = []
    fps_list = []
    times = []
    learning_rates = []
    
    for line in lines:
        # Iterations
        m = re.search(r'\|\s+iterations\s+\|\s+(\d+)', line)
        if m:
            iterations.append(int(m.group(1)))
        
        # Rewards
        m = re.search(r'\|\s+ep_rew_mean\s+\|\s+([-\d.]+)', line)
        if m:
            rewards.append(float(m.group(1)))
        
        # Timesteps
        m = re.search(r'\|\s+total_timesteps\s+\|\s+(\d+)', line)
        if m:
            timesteps.append(int(m.group(1)))
        
        # Explained variance
        m = re.search(r'\|\s+explained_variance\s+\|\s+([-\d.]+)', line)
        if m:
            explained_vars.append(float(m.group(1)))
        
        # Loss
        m = re.search(r'\|\s+loss\s+\|\s+([-\d.]+)', line)
        if m:
            losses.append(float(m.group(1)))
        
        # FPS
        m = re.search(r'\|\s+fps\s+\|\s+(\d+)', line)
        if m:
            fps_list.append(int(m.group(1)))
        
        # Time elapsed
        m = re.search(r'\|\s+time_elapsed\s+\|\s+(\d+)', line)
        if m:
            times.append(int(m.group(1)))
        
        # Learning rate
        m = re.search(r'\|\s+learning_rate\s+\|\s+([-\d.]+)', line)
        if m:
            learning_rates.append(float(m.group(1)))
    
    # Check if process is running
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    is_running = 'train_ppo.py' in result.stdout and '2000000' in result.stdout
    
    print(f'Status: {\"RUNNING\" if is_running else \"STOPPED\"}')
    print(f'Timestamp: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print('')
    print('════════════════════════════════════════════════════════════════')
    print('  TRAINING PROGRESS')
    print('════════════════════════════════════════════════════════════════')
    
    if iterations:
        latest_iter = iterations[-1]
        latest_ts = timesteps[-1] if timesteps else 0
        progress_pct = (latest_ts / 2000000) * 100
        remaining = 2000000 - latest_ts
        
        print(f'Iteration:          {latest_iter}')
        print(f'Total Timesteps:    {latest_ts:,} / 2,000,000 ({progress_pct:.1f}%)')
        print(f'Remaining:          {remaining:,}')
        
        if times:
            elapsed_sec = times[-1]
            elapsed_min = elapsed_sec / 60
            elapsed_hour = elapsed_min / 60
            print(f'Time Elapsed:       {elapsed_min:.1f} min ({elapsed_hour:.2f} hours)')
            
            if latest_ts > 0:
                rate = latest_ts / elapsed_sec
                rate_per_hour = rate * 3600
                remaining_time = remaining / rate if rate > 0 else 0
                remaining_min = remaining_time / 60
                remaining_hour = remaining_min / 60
                
                print(f'Training Rate:      {rate:.0f} timesteps/sec ({rate_per_hour/1000:.0f}k/hour)')
                print(f'Est. Time Left:     {remaining_min:.1f} min ({remaining_hour:.2f} hours)')
        
        print('')
        print('════════════════════════════════════════════════════════════════')
        print('  LEARNING METRICS')
        print('════════════════════════════════════════════════════════════════')
        
        if rewards:
            print(f'Current Reward:     {rewards[-1]:.2f}')
            print(f'Target (Decent):    +12.0 (gap: {12.0 - rewards[-1]:.1f} points)')
            print(f'Target (Good):      +27.0 (gap: {27.0 - rewards[-1]:.1f} points)')
            
            if len(rewards) > 1:
                improvement = rewards[-1] - rewards[0]
                print(f'Net Improvement:    {improvement:+.1f} points')
                
                if len(rewards) >= 2:
                    recent = rewards[-1] - rewards[-2]
                    print(f'Last Iter Change:   {recent:+.1f} points')
        
        if explained_vars:
            ev = explained_vars[-1]
            print(f'Explained Variance: {ev:.4f}', end='')
            if ev > 0.8:
                print(' ✓ Excellent')
            elif ev > 0.5:
                print(' ✓ Good')
            elif ev > 0:
                print(' ⚠ Improving')
            else:
                print(' ✗ Negative')
        
        if losses:
            print(f'Loss:               {losses[-1]:.4f}')
        
        if learning_rates:
            print(f'Learning Rate:      {learning_rates[-1]:.6f}')
        
        if fps_list:
            print(f'Training Speed:     {fps_list[-1]} FPS')
        
        print('')
        print('════════════════════════════════════════════════════════════════')
        print('  REWARD TREND (Last 5 Iterations)')
        print('════════════════════════════════════════════════════════════════')
        
        if len(rewards) >= 1:
            recent_rewards = rewards[-5:] if len(rewards) >= 5 else rewards
            recent_iters = iterations[-len(recent_rewards):] if len(iterations) >= len(recent_rewards) else [i+1 for i in range(len(recent_rewards))]
            
            for i, (iter_num, reward) in enumerate(zip(recent_iters, recent_rewards)):
                arrow = '→' if i < len(recent_rewards) - 1 else '●'
                print(f'  Iter {iter_num:2d}: {reward:7.2f} {arrow}')
        else:
            print('  (No data yet)')
        
        print('')
        print('════════════════════════════════════════════════════════════════')
        
    else:
        print('Training not started or no data yet...')
    
    print('')
    print('Press Ctrl+C to stop monitoring')

except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
PYEOF
"
    
    sleep 5  # Update every 5 seconds
done
