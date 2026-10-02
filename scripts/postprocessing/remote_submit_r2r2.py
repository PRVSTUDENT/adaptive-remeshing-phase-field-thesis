#!/usr/bin/env python3
import os
import sys
import subprocess
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_R2R2_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART2R2"
REMOTE_HOST = "mlogin01.hrz.tu-freiberg.de"
REMOTE_R2R2_DIR = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2"
SSH_KEY = r"C:\Users\pruth\.ssh\id_rsa"

def run_ssh(cmd):
    full_cmd = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", REMOTE_HOST, cmd]
    return subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def main():
    print("=== EXECUTING AUTHORIZED SINGLE SUBMISSION FOR M2STATE_FRACFIX_RESTART2R2 ===")
    
    # 1. Sync files to remote
    print("Step 1: Staging files to cluster...")
    run_ssh(f"mkdir -p {REMOTE_R2R2_DIR}")
    for f in LOCAL_R2R2_DIR.iterdir():
        if f.is_file():
            scp_cmd = ["scp", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", str(f), f"{REMOTE_HOST}:{REMOTE_R2R2_DIR}/"]
            subprocess.run(scp_cmd, check=True)
    print("Staging -> PASS")
    
    # 2. Run guarded wrapper on remote host with --execute
    print("Step 2: Invoking guarded wrapper submit_m2state_fracfix_restart2r2.sh --execute...")
    res_sub = run_ssh(
        f"cd {REMOTE_R2R2_DIR} && "
        "chmod +x submit_m2state_fracfix_restart2r2.sh && "
        "./submit_m2state_fracfix_restart2r2.sh --execute"
    )
    
    print("SUBMISSION_STDOUT:\n", res_sub.stdout)
    print("SUBMISSION_STDERR:\n", res_sub.stderr)
    print("SUBMISSION_RC =", res_sub.returncode)
    
    if res_sub.returncode != 0:
        print("SUBMISSION_FAILED")
        sys.exit(1)
        
    print("=== SUBMISSION SUCCESSFUL ===")

if __name__ == "__main__":
    main()
