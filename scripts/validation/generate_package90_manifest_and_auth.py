#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package90_manifest_and_auth.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates PACKAGE_MANIFEST.json and M1_C3_PACKAGE90_TRANSFER_AUTHORIZATION.json
for Package 90: Candidate C2 -> Candidate C3 Second-Cycle Nonmatching State Transfer.
"""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_c3_package90_second_cycle_transfer"

def get_hash(filename: str) -> str:
    p = PKG_DIR / filename
    return hashlib.sha256(p.read_bytes()).hexdigest().lower()

def main():
    # 1. Write PACKAGE_MANIFEST.json
    manifest = {
        "package_id": "PACKAGE_90_C3_SECOND_CYCLE_TRANSFER",
        "mesh": "Candidate C3 mesh (h_fine=1.0 um in y, 1.25 um in x, 2650 physical quads, 2769 physical nodes)",
        "purpose": "Second-cycle nonmatching coupled state transfer at Package 89 terminal state (u_top=0.002015107 mm, RF2=169.5991 N, d_max=0.85696) from Candidate C2 to forward-adapted Candidate C3 mesh (crack band extended to x in [0.0375, 0.0775] mm). Evaluates: (1) Step 1 state injection force continuity; (2) Step 2 interior mechanical re-equilibration under frozen damage; (3) Step 3 active-set phase subproblem; (4) Step 4 continued forward propagation to u=0.0020651 mm.",
        "files": {
            "inp": "M1_C3_PACKAGE90_TRANSFER.inp",
            "inp_sha256": get_hash("M1_C3_PACKAGE90_TRANSFER.inp").upper(),
            "uel": "f42_mixed_uel.for",
            "uel_sha256": get_hash("f42_mixed_uel.for").upper(),
            "pbs": "submit_M1_C3_PACKAGE90_TRANSFER.pbs",
            "pbs_sha256": get_hash("submit_M1_C3_PACKAGE90_TRANSFER.pbs").upper(),
            "notif": "job_notifications.sh",
            "notif_sha256": get_hash("job_notifications.sh").upper(),
            "datacheck_script": "run_pkg90_datacheck.sh",
            "datacheck_script_sha256": get_hash("run_pkg90_datacheck.sh").upper(),
            "mapped_state_csv": "candidate_c3_frame89_mapped_state_table.csv",
            "mapped_state_csv_sha256": get_hash("candidate_c3_frame89_mapped_state_table.csv").upper()
        }
    }
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote PACKAGE_MANIFEST.json: {manifest_path}")

    # 2. Write Authorization JSON
    cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package90_c3_transfer/submit_M1_C3_PACKAGE90_TRANSFER.pbs"'
    cmd_hash = hashlib.sha256(cmd.encode("utf-8")).hexdigest().lower()

    auth = {
        "batch_name": "MODE1_PACKAGE_90_C3_TRANSFER",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_package90_c3_transfer",
        "files": {
            "M1_C3_PACKAGE90_TRANSFER.inp": get_hash("M1_C3_PACKAGE90_TRANSFER.inp"),
            "f42_mixed_uel.for": get_hash("f42_mixed_uel.for"),
            "job_notifications.sh": get_hash("job_notifications.sh"),
            "submit_M1_C3_PACKAGE90_TRANSFER.pbs": get_hash("submit_M1_C3_PACKAGE90_TRANSFER.pbs"),
            "PACKAGE_MANIFEST.json": get_hash("PACKAGE_MANIFEST.json")
        },
        "jobs": [
            {
                "id": "M1_C3_PACKAGE90_TRANSFER",
                "pbs": "submit_M1_C3_PACKAGE90_TRANSFER.pbs",
                "command": cmd,
                "command_sha256": cmd_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Second-cycle nonmatching coupled state transfer at Package 89 terminal state (u_top=0.002015107 mm, RF2=169.5991 N, d_max=0.85696) from Candidate C2 to forward-adapted Candidate C3 mesh under frozen production UEL",
                "cpus": 1,
                "memory_gb": 8,
                "walltime_hours": 4,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C3_PACKAGE90_TRANSFER.inp",
                "datacheck": "M1_C3_PACKAGE90_TRANSFER_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C3_PACKAGE90_TRANSFER": "Exit code 0 across 4 steps; holding reaction force within 5% of donor C2 terminal RF2 (169.599 N); interior re-equilibration under frozen damage converges; active-set phase subproblem satisfies d >= d_mapped (zero healing); continued forward loading exhibits monotonic crack propagation softening."
        }
    }

    auth_path = PKG_DIR / "M1_C3_PACKAGE90_TRANSFER_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth, f, indent=2)
    print(f"Wrote Authorization JSON: {auth_path}")

if __name__ == "__main__":
    main()
