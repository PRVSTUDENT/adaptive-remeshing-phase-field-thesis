#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package115_manifest.py
Generates M1_C4_INC79_TRANSFER_AUTHORIZATION.json and PACKAGE_MANIFEST.json
for Package 115 (Isolated Increment-79 Direct State-Transfer Control).
"""
import os
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    tracked_files = [
        "M1_C4_INC79_DIRECT_TRANSFER.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c4_inc79_direct_transfer.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "run_c4_inc79_transfer_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C4_INC79_DIRECT_TRANSFER.pbs",
    ]

    files_dict = {}
    for fname in tracked_files:
        fpath = PKG_DIR / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing required package file: {fpath}")
        files_dict[fname] = sha256_file(fpath)

    cmd_prefix = "powershell -NoProfile -ExecutionPolicy Bypass -File .\\."
    cmd_body = "agents\\scripts\\Invoke-GuardedSsh.ps1"
    remote_cmd = ' -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c4_inc79_direct_transfer/submit_M1_C4_INC79_DIRECT_TRANSFER.pbs"'
    cmd = cmd_prefix + cmd_body + remote_cmd
    cmd_sha256 = hashlib.sha256(cmd.encode("utf-8")).hexdigest().lower()

    auth = {
        "schema": 1,
        "adapter": "mode1-experimental-12dof-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C4_INC79_DIRECT_TRANSFER",
        "configuration": "ALTERNATING_MINIMIZATION_SAME_LOAD_DIRECT_TRANSFER",
        "hypothesis": "Directly transferring C3 Increment 79 onto C4 and re-equilibrating at the same physical displacement can distinguish a discretization-related energy offset from errors accumulated during Package 112->113 sequential continuation.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c4_inc79_direct_transfer",
        "files": files_dict,
        "jobs": [
            {
                "id": "M1_C4_INC79_TRANSFER",
                "purpose": "Abaqus 2023 Candidate C4 Stage C1-1 Direct State-Transfer Control at u = 0.00184250 mm (4,422 quads, 4,588 nodes, up to 15 AM cycles with irreversible history transferred from authentic C3 Increment 79)",
                "input": "M1_C4_INC79_DIRECT_TRANSFER.inp",
                "user_subroutine": "f42_unified_12dof_active_set_uel.for",
                "pbs": "submit_M1_C4_INC79_DIRECT_TRANSFER.pbs",
                "datacheck": "M1_C4_INC79_XFER_DC.dat",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": cmd,
                "command_sha256": cmd_sha256,
                "depends_on": []
            }
        ],
        "acceptance": {
            "stage_C1_1_direct_transfer": {
                "u_top_target_mm": 0.0018425,
                "rf2_expected_N": 186.067909,
                "rf2_continuity_pct_max": 5.0,
                "energy_continuity_pct_max": 2.0,
                "kkt_violations_max": 0,
                "free_phase_residual_max_kN_mm": 1e-06,
                "healing_tolerance": 0,
                "stationarity_delta_d_max": 0.001,
                "stationarity_delta_rf2_max_N": 0.1
            }
        },
        "package_name": "115_c4_inc79_direct_transfer"
    }

    manifest = {
        "schema": 1,
        "package_name": "115_c4_inc79_direct_transfer",
        "created_at": "2026-10-27T05:43:00Z",
        "files": files_dict,
        "jobs": auth["jobs"]
    }

    auth_path = PKG_DIR / "M1_C4_INC79_TRANSFER_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth, f, indent=2)

    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {auth_path} (SHA256: {sha256_file(auth_path)})")
    print(f"Generated {manifest_path} (SHA256: {sha256_file(manifest_path)})")

if __name__ == "__main__":
    main()
