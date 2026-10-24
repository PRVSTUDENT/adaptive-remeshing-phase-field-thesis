#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package100_authorization.py
Generates M1_C5_PACKAGE100_PDAS_PILOT_AUTHORIZATION.json with verified file hashes
and execution command SHA-256 for Invoke-Mode1Execution.ps1.
"""
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/100_c5_pdas_snesvi_projected_continuation"
auth_path = pkg_dir / "M1_C5_PACKAGE100_PDAS_PILOT_AUTHORIZATION.json"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

# Files to include in authorization
file_names = [
    "candidate_c5_frame7_mapped_state_table.csv",
    "candidate_crack_band_mesh_c5.inp",
    "extract_pdas_subproblem_odb.py",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "M1_C5_PACKAGE100_SEED_TRANSFER.inp",
    "M1_C5_PACKAGE100_SEED_TRANSFER_DC.dat",
    "PACKAGE_MANIFEST.json",
    "pdas_cluster_execution_adapter.py",
    "run_pkg100_datacheck.sh",
    "submit_M1_C5_PACKAGE100_SNESVI_PILOT.pbs"
]

files_dict = {}
for fname in sorted(file_names):
    p = pkg_dir / fname
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {p}")
    files_dict[fname] = sha256_file(p)

# Remote command string
remote_run_dir = "/scratch9/pr21vyci/runs/mode1_package100_c5_pdas_snesvi_pilot"
pbs_script = "submit_M1_C5_PACKAGE100_SNESVI_PILOT.pbs"
cmd_str = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_run_dir}/{pbs_script}"'
cmd_sha256 = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest().lower()

auth_data = {
    "batch_name": "MODE1_PACKAGE_100_C5_PDAS_SNESVI_PILOT",
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
            "id": "M1_C5_PACKAGE100_SNESVI_PILOT",
            "pbs": pbs_script,
            "command": cmd_str,
            "command_sha256": cmd_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Package 100: Live cluster iterative PDAS pilot on C5 crack-band mesh under Abaqus 2023 with Benson & Munson (2006) / PETSc SNESVI Safeguarded Projected Active-Set Globalization, authentic nodal DOF 3 extraction from .dat, strictly disjoint active-set partitions (U, L, A), cycle-prevention projection extinguishing the 61-node chatter, unscaled authentic history, +4.0 nm continuation loading (u_target=0.002056 mm), and atomic checkpoint persistence.",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "M1_C5_PACKAGE100_SEED_TRANSFER.inp",
            "datacheck": "M1_C5_PACKAGE100_SEED_TRANSFER_DC.dat"
        }
    ],
    "acceptance": {
        "M1_C5_PACKAGE100_SNESVI_PILOT": "Active-set stationarity and valid KKT conditions achieved via SNESVI projected globalization; free-set residual ||R_d||_inf,A <= 1e-6 kN/mm; mechanical equilibrium residual <= 1e-4 kN; reaction force continuity within 5% of authentic Package 94 donor RF2 (112.97 N); fracture energy jump within 2% of donor E_frac (0.00013774 kN*mm); strict irreversibility preserved (0 genuine healing points); strict non-overshoot preserved (d <= 1.000000); authentic committed Gauss-point history H preserved without reset; converged checkpoint pdas_accepted_checkpoint.json emitted."
    }
}

with open(auth_path, "w", encoding="utf-8") as f:
    json.dump(auth_data, f, indent=2)

print(f"Generated {auth_path.name} successfully.")
print(f"Command SHA-256: {cmd_sha256}")
