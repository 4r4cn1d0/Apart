#!/bin/bash
# Optimized training script for 8x H100 Lambda Cloud instance
# Maximum parallelization with enhanced rewards and learning rate schedule

cd ~/game/rl_env
source ~/game/venv/bin/activate

# Training parameters optimized for 8x H100
# 208 vCPUs allow for 128+ parallel environments
# 640 GB GPU memory allows for large batch sizes

python train_ppo.py \
  --total-timesteps 2000000 \
  --n-envs 128 \
  --learning-rate 3e-4 \
  --use-lr-schedule \
  --n-steps 2048 \
  --batch-size 512 \
  --n-epochs 15 \
  --gamma 0.99 \
  --gae-lambda 0.95 \
  --ent-coef 0.01 \
  --max-steps 3000 \
  --max-days 10 \
  --eval-freq 50000 \
  --n-eval-episodes 10 \
  --checkpoint-freq 100000 \
  --tensorboard-log ./tensorboard \
  --save-dir ./models \
  --log-dir ./logs \
  2>&1 | tee training_h100.log

echo "Training complete! Check training_h100.log for output."
