# How to Monitor the Experiment Live

## Quick Commands

### 1. **Watch Live with Colors** (Recommended)
```bash
tail -f experiment_fixed_v2.log
```
- Shows real-time output with ANSI colors
- Press `Ctrl+C` to stop

### 2. **Watch Live without Colors** (Cleaner)
```bash
tail -f experiment_fixed_v2.log | sed -r 's/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g'
```
- Cleaner output, easier to read
- Press `Ctrl+C` to stop

### 3. **See Last N Lines**
```bash
# Last 50 lines
tail -50 experiment_fixed_v2.log

# Last 100 lines
tail -100 experiment_fixed_v2.log

# Last 200 lines (good for seeing full conversations)
tail -200 experiment_fixed_v2.log
```

### 4. **Filter for Specific Content**

**Just Conversations:**
```bash
tail -f experiment_fixed_v2.log | grep -E '\[T[0-9]\]|ACTIONS|Agent [ABC]:'
```

**Just Actions and Stats:**
```bash
tail -f experiment_fixed_v2.log | grep -E 'ACTIONS|Agent [ABC]: L=|Prosperity|DAY'
```

**Just Metrics:**
```bash
tail -f experiment_fixed_v2.log | grep -E 'METRICS|EXPLOITING|EXPLOITED|Elapsed'
```

### 5. **Continuous Clean Text File**
The experiment also creates a clean text version:
```bash
# Check if it exists
cat experiment_fixed_v2.txt

# Watch it (if being updated)
tail -f experiment_fixed_v2.txt
```

## Current Experiment Files

- **Log file (with colors):** `experiment_fixed_v2.log`
- **Text file (clean):** `experiment_fixed_v2.txt` (if created)
- **Run ID:** `fixed_v2_run`

## Check Experiment Status

**Is it still running?**
```bash
ps aux | grep "run_live_30min.*fixed_v2" | grep -v grep
```

**See how long it's been running:**
```bash
ps -p $(pgrep -f "run_live_30min.*fixed_v2") -o etime
```

**Stop the experiment:**
```bash
pkill -f "run_live_30min.*fixed_v2"
```

## Recommended: Watch Live in a New Terminal

1. **Open a new terminal window/tab**
2. **Navigate to the project:**
   ```bash
   cd "/Users/spiderishi/Coding/Apart Pt 2"
   ```
3. **Watch live:**
   ```bash
   tail -f experiment_fixed_v2.log
   ```

This will show you:
- Live conversations between agents
- Actions being taken
- World state updates
- Metrics as episodes complete

Press `Ctrl+C` to stop watching (experiment continues running).
