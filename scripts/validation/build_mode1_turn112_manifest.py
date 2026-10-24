#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_mode1_turn112_manifest.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 112)
Builds the qualified Mode-I execution manifest for the 4-element diagnostic patch.
"""
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET_DIR = REPO_ROOT / "models/pandey_kumar_mode1/104_experimental_irreversible_uel/diagnostic_patch"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

command = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_experimental_diagnostic_patch/submit_M1_DIAG_4ELEM.pbs"'
cmd_sha256 = hashlib.sha256(command.encode("utf-8")).hexdigest().lower()

files = {
    "M1_DIAGNOSTIC_4ELEM_IRREV.inp": sha256_file(TARGET_DIR / "M1_DIAGNOSTIC_4ELEM_IRREV.inp"),
    "d_lower_bounds.csv": sha256_file(TARGET_DIR / "d_lower_bounds.csv"),
    "f42_experimental_irreversible_uel.for": sha256_file(TARGET_DIR / "f42_experimental_irreversible_uel.for"),
    "submit_M1_DIAG_4ELEM.pbs": sha256_file(TARGET_DIR / "submit_M1_DIAG_4ELEM.pbs"),
    "job_notifications.sh": sha256_file(TARGET_DIR / "job_notifications.sh"),
    "run_datacheck.sh": sha256_file(TARGET_DIR / "run_datacheck.sh")
}

manifest = {
    "batch_name": "MODE1_EXPERIMENTAL_DIAGNOSTIC_4ELEM",
    "scientific_scope": "MODE1",
    "adapter": "mode1-qualified-batch-v2",
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_experimental_diagnostic_patch",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": files,
    "jobs": [
        {
            "id": "diag_4elem",
            "pbs": "submit_M1_DIAG_4ELEM.pbs",
            "command": command,
            "command_sha256": cmd_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "4-Element diagnostic patch verification of experimental irreversible UEL (damage retention in Stage A, damage advancement in Stage B)",
            "cpus": 1,
            "memory_gb": 8,
            "walltime_hours": 1,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "M1_DIAGNOSTIC_4ELEM_IRREV.inp",
            "datacheck": "M1_DIAG_DC.dat"
        }
    ],
    "acceptance": {
        "diag_4elem": "Stage A damage healing <= 1e-8 at central shared node 5 (d5 >= 0.6000 under H=0.05 kN/mm^2); Stage B strictly positive damage advancement (d5 advances to ~0.965 under H=2.50 kN/mm^2); Newton convergence Exit 0; all acceptance gates pass."
    }
}

manifest_path = TARGET_DIR / "M1_DIAGNOSTIC_AUTHORIZATION.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Created {manifest_path}")
print("Files in manifest:")
for k, v in files.items():
    print(f"  {k}: {v}")
print(f"Command SHA256: {cmd_sha256}")
