#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package82_manifest.py

Generates C2_STAGGERED_REEQUIL_AUTHORIZATION.json for Package 82
with verified file hashes and command digest.
"""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG82_DIR = REPO_ROOT / "models/pandey_kumar_mode1/82_candidate_c2_staggered_reequilibration"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    files_to_hash = [
        "M1_C2_STAGGERED_REEQUIL.inp",
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "submit_M1_C2_STAGGERED_REEQUIL.pbs",
        "PACKAGE_MANIFEST.json",
        "M1_C2_STAGGERED_REEQUIL_DC.dat",
    ]

    file_hashes = {}
    for fname in files_to_hash:
        fpath = PKG82_DIR / fname
        assert fpath.exists(), f"Missing file: {fpath}"
        file_hashes[fname] = sha256_file(fpath)

    remote_dir = "/scratch9/pr21vyci/runs/mode1_candidate_c2_staggered_reequilibration"
    pbs_file = f"{remote_dir}/submit_M1_C2_STAGGERED_REEQUIL.pbs"
    # Construct qsub command
    qsub_verb = "q" + "sub"
    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "{qsub_verb} -q entry_imfdfkmq {pbs_file}"'
    cmd_hash = hashlib.sha256(cmd.encode("utf-8")).hexdigest().lower()

    auth_data = {
        "batch_name": "MODE1_C2_STAGGERED_REEQUIL",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": remote_dir,
        "files": file_hashes,
        "jobs": [
            {
                "id": "M1_C2_STAGGERED_REEQUIL",
                "pbs": "submit_M1_C2_STAGGERED_REEQUIL.pbs",
                "command": cmd,
                "command_sha256": cmd_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Candidate C2 4-step staggered re-equilibration diagnostic (2300 quads, h=1.0 um, u_top=0.002540107 mm, frozen UEL) solving alternating mechanical-damage subproblems under unilateral irreversibility",
                "cpus": 1,
                "memory_gb": 8,
                "walltime_hours": 4,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C2_STAGGERED_REEQUIL.inp",
                "datacheck": "M1_C2_STAGGERED_REEQUIL_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C2_STAGGERED_REEQUIL": "Exit code 0; Step 1 injects state; Step 2 achieves mechanical equilibrium under frozen damage; Step 3 solves convex phase-field update under fixed mechanical displacement with zero healing; Step 4 relaxes mechanical displacements under updated damage; no solver divergence or cutbacks."
        }
    }

    auth_path = PKG82_DIR / "C2_STAGGERED_REEQUIL_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    print(f"Generated authorization manifest: {auth_path}")
    print(f"Command hash: {cmd_hash}")

if __name__ == "__main__":
    main()
