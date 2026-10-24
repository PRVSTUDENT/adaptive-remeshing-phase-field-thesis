#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package101_authorization.py
Generates M1_C5_PACKAGE101_VI_PILOT_AUTHORIZATION.json with verified file hashes
and execution command SHA-256 for Invoke-Mode1Execution.ps1.
"""
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/101_c5_bound_constrained_vi_continuation"
auth_path = pkg_dir / "M1_C5_PACKAGE101_VI_PILOT_AUTHORIZATION.json"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def generate():
    # Files to include in authorization
    file_names = [
        "candidate_c5_frame7_mapped_state_table.csv",
        "candidate_crack_band_mesh_c5.inp",
        "extract_pdas_subproblem_odb.py",
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "M1_C5_PACKAGE101_SEED_TRANSFER.inp",
        "M1_C5_PACKAGE101_SEED_TRANSFER_DC.dat",
        "PACKAGE_MANIFEST.json",
        "vi_cluster_execution_adapter.py",
        "run_pkg101_datacheck.sh",
        "submit_M1_C5_PACKAGE101_VI_PILOT.pbs"
    ]

    files_dict = {}
    for fname in sorted(file_names):
        p = pkg_dir / fname
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {p}")
        files_dict[fname] = sha256_file(p)

    remote_run_dir = "/scratch9/pr21vyci/runs/mode1_package101_c5_vi_continuation"
    pbs_script = "submit_M1_C5_PACKAGE101_VI_PILOT.pbs"
    cmd_str = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_run_dir}/{pbs_script}"'
    cmd_sha256 = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest().lower()

    auth_data = {
        "batch_name": "MODE1_PACKAGE_101_C5_VI_PILOT",
        "adapter": "mode1-pdas-iterative-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": remote_run_dir,
        "files": files_dict,
        "jobs": [
            {
                "id": "M1_C5_PACKAGE101_VI_PILOT",
                "pbs": pbs_script,
                "command": cmd_str,
                "command_sha256": cmd_sha256,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 101: Live cluster bound-constrained VI pilot on C5 crack-band mesh solving min_{d_ckpt <= d <= 1.0} (1/2 d^T K d - F^T d) to exact KKT stationarity (||R_d||_inf,A <= 1e-6 kN/mm), replacing Package 100 release suppression heuristic with true variational inequality optimization, enforcing zero damage healing and zero overshoot by construction, and coupling mechanical equilibrium in Abaqus 2023 under frozen UEL.",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C5_PACKAGE101_SEED_TRANSFER.inp",
                "datacheck": "M1_C5_PACKAGE101_SEED_TRANSFER_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C5_PACKAGE101_VI_PILOT": "Bound-constrained VI stationarity and valid KKT conditions achieved without heuristic release suppression; free-set residual ||R_d||_inf,A <= 1e-6 kN/mm; lower-bound KKT multipliers valid (lambda_L <= 1e-6 kN/mm); upper-bound KKT multipliers valid; reaction force continuity within 5% of authentic Package 94 donor RF2 (112.97 N); fracture energy jump within 2% of donor E_frac (0.00013774 kN*mm); strict irreversibility preserved (0 genuine healing points); strict non-overshoot preserved (d <= 1.000000); authentic committed Gauss-point history H preserved without reset; converged checkpoint pdas_accepted_checkpoint.json emitted."
        }
    }

    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    print(f"Generated {auth_path.name} successfully.")
    print(f"Command SHA-256: {cmd_sha256}")

if __name__ == "__main__":
    generate()
