#!/usr/bin/env python3
import os
import subprocess
import json
import sys
from pathlib import Path

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"
ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02"
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

def main():
    # 1. SCP the standalone extractor
    script_local = ROOT / "scripts/postprocessing/extract_1389229_summary_remote.py"
    cmd_scp = ["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", str(script_local), f"{REMOTE_HOST}:{REMOTE_CANDIDATE}/extract_1389229_summary_remote.py"]
    print("--> SCP extract script...")
    res = subprocess.run(cmd_scp, capture_output=True, text=True)
    print(res.stdout)

    # 2. Run with abaqus python
    remote_cmd = (
        f"source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
        f"module purge && "
        f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        f"cd {REMOTE_CANDIDATE} && "
        f"abaqus python extract_1389229_summary_remote.py"
    )
    cmd_run = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, remote_cmd]
    print("--> Running remote abaqus python...")
    res_run = subprocess.run(cmd_run, capture_output=True, text=True)
    print(res_run.stdout)
    if res_run.stderr:
        print("STDERR:", res_run.stderr, file=sys.stderr)

    # 3. Pull summary json and logs
    print("--> Fetching summary artifacts...")
    files = ["EXECUTION_SUMMARY.json", "M2STATE_FRACFIX_RESTART2R7.prt", "M2STATE_FRACFIX_RESTART2R7.com"]
    for f in files:
        scp_cmd = ["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", f"{REMOTE_HOST}:{REMOTE_CANDIDATE}/{f}", str(LOCAL_DIR / f)]
        subprocess.run(scp_cmd, capture_output=True)
        print(f"  Fetched: {f}")

    pbs_pull = f"scp -i {SSH_KEY} -o BatchMode=yes -o StrictHostKeyChecking=no {REMOTE_HOST}:{REMOTE_CANDIDATE}/M2STATE_FRACFIX_RESTART2R7.o* \"{LOCAL_DIR}/\""
    subprocess.run(pbs_pull, shell=True, capture_output=True)
    print("  Fetched PBS log.")

if __name__ == "__main__":
    main()
