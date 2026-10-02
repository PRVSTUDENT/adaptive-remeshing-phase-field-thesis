#!/usr/bin/env python3
"""
Remote Submission Driver for Candidate M2STATE_FRACFIX_RESTART2R7
Task ID: F77STATE-M2-RESTART2R7-EXECUTE1
Target: mlogin01.hrz.tu-freiberg.de
"""

import os
import subprocess
import json
import sys

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"

def main():
    print("======================================================================")
    print("EXECUTING SINGLE AUTHORIZED SUBMISSION: M2STATE_FRACFIX_RESTART2R7")
    print("======================================================================")

    submit_cmd = (
        f"cd {REMOTE_CANDIDATE} && "
        f"./submit_m2state_fracfix_restart2r7.sh --execute"
    )

    cmd = [
        "ssh", "-i", SSH_KEY,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        REMOTE_HOST,
        submit_cmd
    ]

    print(f"--> Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr, file=sys.stderr)
    print(f"Exit Code: {res.returncode}")

    if res.returncode != 0:
        raise RuntimeError(f"Submission wrapper failed with return code {res.returncode}")

if __name__ == "__main__":
    main()
