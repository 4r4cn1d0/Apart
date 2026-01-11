#!/bin/bash
# Run multiple 30-minute experiments in parallel

NUM_RUNS=${1:-3}  # Default to 3 parallel runs
DURATION=${2:-30}  # Default to 30 minutes

echo "=========================================="
echo "Starting $NUM_RUNS parallel experiments"
echo "Duration: ${DURATION} minutes each"
echo "=========================================="
echo ""

export LAMBDA_API_KEY='secret_game_71e6ce0a7995456598bf08bcdc0eda0f.NYYvPzJolHgwv0X3nqY5GxPZ5hONgQRk'

PIDS=()
for i in $(seq 1 $NUM_RUNS); do
    RUN_ID="run${i}_$(date +%s)"
    echo "Starting experiment $i (Run ID: $RUN_ID)..."
    python3 run_live_30min.py --duration $DURATION --run-id $RUN_ID > experiment_${i}.log 2>&1 &
    PID=$!
    PIDS+=($PID)
    echo "  ✓ Experiment $i started (PID: $PID, Run ID: $RUN_ID)"
    echo "  Log: experiment_${i}.log"
    echo "  Results: experiment_metrics_${RUN_ID}.csv"
    sleep 3  # Stagger starts slightly to avoid API overload
    echo ""
done

echo "=========================================="
echo "All $NUM_RUNS experiments started!"
echo "=========================================="
echo ""
echo "Monitor all logs:"
echo "  tail -f experiment_*.log"
echo ""
echo "Monitor specific experiment:"
echo "  tail -f experiment_1.log"
echo ""
echo "Check running processes:"
echo "  ps aux | grep run_live_30min"
echo ""
echo "Stop all experiments:"
echo "  pkill -f 'run_live_30min.py'"
echo ""
echo "PIDs: ${PIDS[@]}"
