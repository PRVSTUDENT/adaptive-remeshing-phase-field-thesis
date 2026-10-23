#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer"

def get_hash(filename):
    p = PKG_DIR / filename
    return hashlib.sha256(p.read_bytes()).hexdigest().lower()

cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package89_c2_frame88_transfer/submit_M1_C2_FRAME88_TRANSFER.pbs"'
cmd_canonical = ' '.join(cmd.strip().split())
cmd_hash = hashlib.sha256(cmd_canonical.encode('utf-8')).hexdigest().lower()

manifest = {
    "batch_name": "MODE1_PACKAGE_89_C2_FRAME88_TRANSFER",
    "adapter": "mode1-qualified-batch-v2",
    "scientific_scope": "MODE1",
    "technical_stage": "MODE1_BASELINE",
    "configuration": "MODE1_BASELINE",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_package89_c2_frame88_transfer",
    "files": {
        "M1_C2_FRAME88_TRANSFER.inp": get_hash("M1_C2_FRAME88_TRANSFER.inp"),
        "f42_mixed_uel.for": get_hash("f42_mixed_uel.for"),
        "job_notifications.sh": get_hash("job_notifications.sh"),
        "submit_M1_C2_FRAME88_TRANSFER.pbs": get_hash("submit_M1_C2_FRAME88_TRANSFER.pbs"),
        "PACKAGE_MANIFEST.json": get_hash("PACKAGE_MANIFEST.json")
    },
    "jobs": [
        {
            "id": "M1_C2_FRAME88_TRANSFER",
            "pbs": "submit_M1_C2_FRAME88_TRANSFER.pbs",
            "command": cmd,
            "command_sha256": cmd_hash,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Nonmatching coupled state transfer at authentic pre-peak checkpoint Frame 88 (u_top=0.001965107 mm, t=0.39302148 s) from Package 76 visual donor to Candidate C2 mesh under frozen production UEL",
            "cpus": 1,
            "memory_gb": 8,
            "walltime_hours": 4,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "M1_C2_FRAME88_TRANSFER.inp",
            "datacheck": "M1_C2_FRAME88_TRANSFER_DC.dat"
        }
    ],
    "acceptance": {
        "M1_C2_FRAME88_TRANSFER": "Exit code 0 across 4 steps; holding reaction force within 5% of donor (185.335 N); interior re-equilibration under frozen damage converges; active-set phase subproblem satisfies d >= d_mapped (zero healing); continued forward loading exhibits monotonic crack propagation softening."
    }
}

out_path = PKG_DIR / "M1_C2_FRAME88_TRANSFER_AUTHORIZATION.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("Generated Authorization JSON:", out_path)
print("Command:", cmd)
print("Command SHA256:", cmd_hash)
