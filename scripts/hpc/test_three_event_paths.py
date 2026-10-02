#!/usr/bin/env python3
"""Execute the 3 controlled Telegram test paths using the actual job_notifications.sh functions."""
import os
import subprocess
import sys
import json
from pathlib import Path

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import os, subprocess, json, sys

sh_test = '''
set -e
source /home/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_load_config

# 1. Test SUBMITTED path
notify_submitted "TEST_JOB_999999" "M2STATE_SYNTHETIC_TEST" "Synthetic notification-path test. NO PBS JOB WAS SUBMITTED."
echo "SUBMITTED_PASS"

# 2. Test STARTED path
PBS_JOBNAME="M2STATE_SYNTHETIC_TEST" PBS_JOBID="TEST_JOB_999999" notify_start
echo "STARTED_PASS"

# 3. Test COMPLETED path
notify_completed "M2STATE_SYNTHETIC_TEST" "TEST_JOB_999999" 0
echo "COMPLETED_PASS"
'''

res = subprocess.run(["bash", "-c", sh_test], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print("STDOUT:")
print(res.stdout)
if res.stderr:
    print("STDERR:")
    print(res.stderr)
print("RC:", res.returncode)

submitted_pass = "SUBMITTED_PASS" in res.stdout
started_pass = "STARTED_PASS" in res.stdout
completed_pass = "COMPLETED_PASS" in res.stdout

print(json.dumps({
    "telegram_submitted_path_test": "PASS" if submitted_pass else "FAIL",
    "telegram_started_path_test": "PASS" if started_pass else "FAIL",
    "telegram_terminal_path_test": "PASS" if completed_pass else "FAIL",
    "overall_rc": res.returncode
}))
"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        f"python3 -c {subprocess.list2cmdline([remote_script])}"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if res.returncode != 0:
        print("SSH Error:", res.stderr)
        sys.exit(1)
    
    print("THREE EVENT PATH TEST RESULTS:")
    print(res.stdout)

if __name__ == "__main__":
    main()
