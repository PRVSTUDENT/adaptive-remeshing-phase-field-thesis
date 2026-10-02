#!/usr/bin/env python3
"""
Remote Submission Script for Candidate M2STATE_FRACFIX_RESTART1R1R8.
Task ID: F85SUB-M2-CORRECTED-RESTART1-R1R8-PRODUCTION-SUBMISSION1
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8'

    remote_script = f"""#!/bin/bash
set -e
export XDG_RUNTIME_DIR=/tmp/pr21vyci-runtime
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

cd "{remote_pkg_dir}"

echo "=== 1. PRE-SUBMISSION MANIFEST VERIFICATION ==="
python3 validate_package_manifest.py PACKAGE_MANIFEST.json

echo "=== 2. EXECUTING GUARDED WRAPPER SUBMISSION ==="
chmod +x submit_m2state_fracfix_restart1r1r8.sh M2STATE_FRACFIX_RESTART1R1R8.pbs
./submit_m2state_fracfix_restart1r1r8.sh

echo "=== 3. CHECKING QUEUE STATUS ==="
qstat -u pr21vyci
"""

    clean_bytes = remote_script.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'bash -s']
    res = subprocess.run(cmd, input=clean_bytes, capture_output=True)
    stdout = res.stdout.decode('utf-8', errors='replace')
    stderr = res.stderr.decode('utf-8', errors='replace')
    print("STDOUT:\n", stdout)
    print("STDERR:\n", stderr)

if __name__ == "__main__":
    main()
