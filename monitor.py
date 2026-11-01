"""Frozen evidence only. No network, live telemetry, or answers/rubrics."""
import json,sys
from pathlib import Path
commands=json.loads(Path(__file__).with_name('evidence.json').read_text())
command=' '.join(sys.argv[1:])
if command not in commands:
    print('Usage: python monitor.py '+ '\n       python monitor.py '.join(commands))
    raise SystemExit(2)
print('\n'.join(commands[command]))
