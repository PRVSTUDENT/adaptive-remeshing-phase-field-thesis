#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path

R13_DIR = Path("D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set")

files = [
    "M1_C3_ACTIVE_SET_R13_CONTINUATION.inp",
    "f42_unified_12dof_active_set_uel.for",
    "stage_a_all_d0_boundary_cards.inc",
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_r13_autonomous_continuation.py",
    "run_pkg108_r13_datacheck.sh",
    "submit_M1_C3_ACTIVE_SET_R13.pbs",
    "job_notifications.sh"
]

file_hashes_lower = {}
for fname in files:
    p = R13_DIR / fname
    h = hashlib.sha256(p.read_bytes()).hexdigest().lower()
    file_hashes_lower[fname] = h

manifest = {
    "package_name": "PACKAGE_108_R13_C3_AUTONOMOUS_ACTIVE_SET",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "turn": 143,
    "model": "pandey_kumar_mode1",
    "continuation_step": "C3",
    "displacement_increment_nm": 1.0,
    "target_rp_u2_mm": 0.00196610735,
    "formulation": "UNIFIED_12DOF_MONOLITHIC_COUPLED_UEL_AUTONOMOUS_ACTIVE_SET",
    "files": {k: v.upper() for k, v in file_hashes_lower.items()}
}
(R13_DIR / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

cmd_str = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r13/submit_M1_C3_ACTIVE_SET_R13.pbs"'
cmd_sha = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest()

auth = {
    "schema": 1,
    "adapter": "mode1-experimental-12dof-v1",
    "scientific_scope": "MODE1",
    "technical_stage": "C1-1",
    "batch_name": "MODE1_C3_ACTIVE_SET_CONTINUATION_R13",
    "configuration": "UNIFIED_12DOF_AUTONOMOUS_ACTIVE_SET",
    "hypothesis": "Deploying the corrected repository-compatible autonomous active-set iteration driver in genuine Abaqus/Standard 2023 eliminates R11 damage locking without precomputed masks, iteratively discovers active crack-tip constraints via KKT multipliers (lambda = RF3), relaxes reaction force monotonically toward reference continuation, and preserves strict Stage-A checkpoint reset semantics.",
    "automatic_retry": False,
    "max_submissions": 1,
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r13",
    "files": file_hashes_lower,
    "jobs": [
        {
            "id": "M1_C3_ACTIVE_SET_R13",
            "purpose": "Abaqus 2023 Candidate C3 autonomous active-set continuation driver (R13)",
            "input": "M1_C3_ACTIVE_SET_R13_CONTINUATION.inp",
            "user_subroutine": "f42_unified_12dof_active_set_uel.for",
            "pbs": "submit_M1_C3_ACTIVE_SET_R13.pbs",
            "datacheck": "M1_C3_ACTIVE_SET_R13.dat",
            "queue": "entry_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "execution": "single-rank serial",
            "max_submissions": 1,
            "command": cmd_str,
            "command_sha256": cmd_sha,
            "depends_on": []
        }
    ],
    "acceptance": {
        "stage_A_same_load": {
            "u_top_target_mm": 0.00196510735,
            "rf2_expected_N": 184.851,
            "rf2_continuity_pct_max": 1.0,
            "kkt_violations_max": 0
        },
        "stage_B_forward_continuation": {
            "delta_u_mm": 1e-06,
            "u_top_target_mm": 0.00196610735,
            "expected_rf2_N_approx": 180.5077,
            "rf2_tolerance_pct": 2.0,
            "expected_allse_mJ_approx": 0.1818,
            "allse_tolerance_pct": 2.0,
            "expected_dmax_approx": 0.7006,
            "dmax_tolerance_pct": 5.0,
            "kkt_violations_max": 0,
            "healing_magnitude_max": 1e-08
        }
    }
}
(R13_DIR / "M1_C3_ACTIVE_SET_R13_AUTHORIZATION.json").write_text(json.dumps(auth, indent=2), encoding="utf-8")
print("Updated PACKAGE_MANIFEST.json and M1_C3_ACTIVE_SET_R13_AUTHORIZATION.json successfully.")
