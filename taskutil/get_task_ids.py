#!/var/lib/crunch.io/venv/bin/python
"""
Parse task IDs from output of "inspect active" command

On a backend server run:

cr.server.worker cr.server-0.conf inspect active --no-color | ./get_task_ids.py
"""
from __future__ import print_function
import ast
import re
import sys


WORKER_PATTERN = re.compile(r"^-> (\S+): OK$")
TASK_PATTERN = re.compile(r"^\s+\*\s+(.*)\s*$")

def main():
    cur_worker = None
    for line in sys.stdin:
        m = WORKER_PATTERN.search(line)
        if m:
            cur_worker = m.group(1)
            print(cur_worker)
            continue
        m = TASK_PATTERN.search(line)
        if m:
            params_str = m.group(1)
            try:
                params = ast.literal_eval(params_str)
            except ValueError:
                continue
            task_id = params.get("id")
            if task_id:
                print("   ", task_id)


if __name__ == "__main__":
    sys.exit(main())
