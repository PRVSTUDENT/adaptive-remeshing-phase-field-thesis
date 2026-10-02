#!/usr/bin/env python3
"""
Evidence Salvager for Job 1389328.mmaster02 (M2STATE_FRACFIX_RESTART2R14)
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02"
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_PKG_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"

def salvage():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        "M2STATE_FRACFIX_RESTART2R14.sta",
        "M2STATE_FRACFIX_RESTART2R14.msg",
        "M2STATE_FRACFIX_RESTART2R14.pbs.log",
        "M2STATE_FRACFIX_RESTART2R14.prt",
        "M2STATE_FRACFIX_RESTART2R14.com",
        "M2STATE_FRACFIX_RESTART2R14.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R14.pbs",
        "submit_m2state_fracfix_restart2r14.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json",
        "M2STATE_FRACFIX_RESTART2R14.dat"
    ]
    
    for fn in files:
        print(f"Downloading {fn}...")
        local_fp = EVIDENCE_DIR / fn
        scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{REMOTE_PKG_DIR}/{fn}", str(local_fp)]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  Downloaded {fn} ({local_fp.stat().st_size} bytes)")
        else:
            print(f"  Warning: could not download {fn}: {res.stderr}")

if __name__ == '__main__':
    salvage()
