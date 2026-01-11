#!/bin/bash
# Continuously update .txt file from .log file

LOG_FILE="experiment_fixed.log"
TXT_FILE="experiment_fixed.txt"

python3 << 'PYEOF'
import re
import time
from pathlib import Path

log_file = Path("experiment_fixed.log")
txt_file = Path("experiment_fixed.txt")
last_size = 0

def strip_ansi(text):
    ansi_escape = re.compile(r'(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

while True:
    try:
        if log_file.exists():
            current_size = log_file.stat().st_size
            if current_size != last_size:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                clean = strip_ansi(content)
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(clean)
                last_size = current_size
        time.sleep(2)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(2)
PYEOF
