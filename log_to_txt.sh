#!/bin/bash
# Continuous logger - strips ANSI codes and saves to .txt

LOG_FILE="experiment_fixed.log"
TXT_FILE="experiment_fixed.txt"

# Initialize txt file with current log content (stripped)
python3 << 'PYEOF'
import re
try:
    with open("experiment_fixed.log", "r") as f:
        content = f.read()
    ansi_escape = re.compile(r'(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean = ansi_escape.sub('', content)
    with open("experiment_fixed.txt", "w") as f:
        f.write(clean)
except:
    pass
PYEOF

# Tail and append new lines (stripped)
tail -f "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
    echo "$line" | sed "s/\[[0-9;]*[JKmsu]//g" >> "$TXT_FILE"
done
