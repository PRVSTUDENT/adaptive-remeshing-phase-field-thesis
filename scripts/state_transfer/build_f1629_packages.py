#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_f1629_packages.py
=======================
Builds Package 174 (M1_C6_R12_PICARD_BASELINE) and Package 175 (M1_C6_R12_ANDERSON_M2)
from qualified Package 171-R12 for Task F1629 paired controlled overnight execution.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PKG = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r12_c3_0_adaptive_reequilibration"
PKG_174 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "174_c6_r12_picard_baseline"
PKG_175 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "175_c6_r12_anderson_m2"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def build():
    print("=" * 80)
    print("BUILDING F1629 PACKAGES: 174 (PICARD BASELINE) & 175 (ANDERSON M2)")
    print("=" * 80)

    # 1. Create directories
    PKG_174.mkdir(parents=True, exist_ok=True)
    PKG_175.mkdir(parents=True, exist_ok=True)

    # 2. Files to copy from qualified Package 171-R12
    files_to_copy = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "M1_C6_PACKAGE171_R12_C3_0_ADAPTIVE_REEQUILIBRATION.inp",
        "P171_ITER1_MECH.inp",
        "P171_ITER1_PHASE.inp",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "smoke_import.py",
        "run_datacheck.sh",
        "P171_MECHANICAL_DC.dat",
        "P171_MECHANICAL_DC.msg",
        "P171_PHASE_DC.dat",
        "P171_PHASE_DC.msg",
        "P171_ITER1_MECH.dat",
        "P171_ITER1_MECH.msg",
        "P171_ITER1_PHASE.dat",
        "P171_ITER1_PHASE.msg",
    ]

    for f_name in files_to_copy:
        src = SRC_PKG / f_name
        assert src.is_file(), f"Missing source file: {src}"
        shutil.copy2(src, PKG_174 / f_name)
        shutil.copy2(src, PKG_175 / f_name)

    print(f"Copied {len(files_to_copy)} identical base files to Package 174 and 175.")

    # 3. Create PBS scripts with strict LF line endings
    pbs_174_content = """#!/bin/bash
#PBS -N M1_C6_R12_PICARD_BASELINE
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline"
cd "${RUN_DIR}"

export JOB_NAME="M1_C6_R12_PICARD_BASELINE"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${RUN_DIR}/runtime"
python3 "${repo}/scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/equilibration_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 140 \\
    --omega-d-stage1 0.50 \\
    --omega-d-stage2 0.85 \\
    --omega-u-stage1 1.00 \\
    --omega-u-stage2 0.85 \\
    --no-anderson \\
    --max-active-cardinality 500 \\
    --max-symmetric-diff 10 \\
    --max-added-nodes 0 \\
    --stabilization-window 3 \\
    --rollback-factor 1.05 \\
    --divergence-factor 1.50 \\
    --catastrophic-delta-d-cap 0.05
EXIT_CODE=$?

echo "Stage C3-0 Re-equilibration (Job A: Picard Baseline, Anderson Disabled) finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    pbs_174_path = PKG_174 / "submit_M1_C6_R12_PICARD_BASELINE.pbs"
    pbs_174_path.write_bytes(pbs_174_content.replace("\r\n", "\n").encode("utf-8"))

    pbs_175_content = """#!/bin/bash
#PBS -N M1_C6_R12_ANDERSON_M2
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2"
cd "${RUN_DIR}"

export JOB_NAME="M1_C6_R12_ANDERSON_M2"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${RUN_DIR}/runtime"
python3 "${repo}/scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/equilibration_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 140 \\
    --omega-d-stage1 0.50 \\
    --omega-d-stage2 0.85 \\
    --omega-u-stage1 1.00 \\
    --omega-u-stage2 0.85 \\
    --enable-anderson \\
    --anderson-memory 2 \\
    --anderson-beta 0.85 \\
    --anderson-reg 1e-6 \\
    --anderson-gamma-max 200.0 \\
    --anderson-max-step-cap 0.045 \\
    --max-active-cardinality 500 \\
    --max-symmetric-diff 10 \\
    --max-added-nodes 0 \\
    --stabilization-window 3 \\
    --rollback-factor 1.05 \\
    --divergence-factor 1.50 \\
    --catastrophic-delta-d-cap 0.05
EXIT_CODE=$?

echo "Stage C3-0 Re-equilibration (Job B: Safeguarded Anderson M2) finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    pbs_175_path = PKG_175 / "submit_M1_C6_R12_ANDERSON_M2.pbs"
    pbs_175_path.write_bytes(pbs_175_content.replace("\r\n", "\n").encode("utf-8"))

    # 4. Generate PACKAGE_MANIFEST.json for each package
    for pkg, pbs_name, candidate_name in [
        (PKG_174, "submit_M1_C6_R12_PICARD_BASELINE.pbs", "M1_C6_R12_PICARD_BASELINE"),
        (PKG_175, "submit_M1_C6_R12_ANDERSON_M2.pbs", "M1_C6_R12_ANDERSON_M2"),
    ]:
        manifest_path = pkg / "PACKAGE_MANIFEST.json"
        files_dict = {}
        for p in sorted(pkg.iterdir()):
            if p.is_file() and p.name != "PACKAGE_MANIFEST.json":
                files_dict[p.name] = {
                    "sha256": sha256_file(p),
                    "size_bytes": p.stat().st_size
                }
        manifest = {
            "package_name": pkg.name,
            "candidate": candidate_name,
            "task_id": "F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION",
            "predecessor_task_id": "F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR",
            "files_count": len(files_dict),
            "files": files_dict
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    # 5. Build Mode-I Authorization Manifests for Invoke-Mode1Execution.ps1
    runtime_source_files = [
        "scripts/state_transfer/anderson_acceleration.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py",
        "scripts/validation/extract_package148_iteration.py",
    ]
    runtime_source_hashes = {f: sha256_file(REPO_ROOT / f) for f in runtime_source_files}

    # Package 174 Authorization Manifest
    files_174_lower = {p.name: sha256_file(p).lower() for p in sorted(PKG_174.iterdir()) if p.is_file() and not p.name.endswith("_AUTHORIZATION.json")}
    cmd_174 = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline/submit_M1_C6_R12_PICARD_BASELINE.pbs"'
    auth_174 = {
        "batch_name": "MODE1_M1_C6_R12_PICARD_BASELINE",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline/runtime",
        "runtime_source_hashes": runtime_source_hashes,
        "files": files_174_lower,
        "scientific_predecessor_review": "Independent supervisor review decision under correlation HND-9cef512db772 accepting F1629 technical failure classification and registering F1630 pending independent execution review",
        "jobs": [
            {
                "id": "M1_C6_R12_PICARD_BASELINE",
                "pbs": "submit_M1_C6_R12_PICARD_BASELINE.pbs",
                "command": cmd_174,
                "command_sha256": hashlib.sha256(cmd_174.encode("utf-8")).hexdigest(),
                "input": "P171_MECHANICAL_DC.inp",
                "datacheck": "P171_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P171_PHASE_DC.dat"
                ],
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Arm A: C6 R12 adaptive re-equilibration with gradient-preserving isoparametric GP transfer, Anderson DISABLED (Picard baseline)",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial"
            }
        ],
        "acceptance": {
            "M1_C6_R12_PICARD_BASELINE": "C6 R12 adaptive re-equilibration (Arm A): Delta d <= 1e-5, Delta u <= 1e-9 mm, Delta H <= 1e-4 MPa, final KKT <= 1e-6, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        }
    }
    with open(PKG_174 / "M1_C6_R12_PICARD_BASELINE_AUTHORIZATION.json", "w", encoding="utf-8") as f:
        json.dump(auth_174, f, indent=2)

    # Package 175 Authorization Manifest
    files_175_lower = {p.name: sha256_file(p).lower() for p in sorted(PKG_175.iterdir()) if p.is_file() and not p.name.endswith("_AUTHORIZATION.json")}
    cmd_175 = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2/submit_M1_C6_R12_ANDERSON_M2.pbs"'
    auth_175 = {
        "batch_name": "MODE1_M1_C6_R12_ANDERSON_M2",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2/runtime",
        "runtime_source_hashes": runtime_source_hashes,
        "files": files_175_lower,
        "scientific_predecessor_review": "Independent supervisor review decision under correlation HND-9cef512db772 accepting F1629 technical failure classification and registering F1630 pending independent execution review",
        "jobs": [
            {
                "id": "M1_C6_R12_ANDERSON_M2",
                "pbs": "submit_M1_C6_R12_ANDERSON_M2.pbs",
                "command": cmd_175,
                "command_sha256": hashlib.sha256(cmd_175.encode("utf-8")).hexdigest(),
                "input": "P171_MECHANICAL_DC.inp",
                "datacheck": "P171_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P171_PHASE_DC.dat"
                ],
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Arm B: C6 R12 adaptive re-equilibration with gradient-preserving isoparametric GP transfer, safeguarded Anderson ENABLED (m=2, beta=0.85)",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial"
            }
        ],
        "acceptance": {
            "M1_C6_R12_ANDERSON_M2": "C6 R12 adaptive re-equilibration (Arm B): Delta d <= 1e-5, Delta u <= 1e-9 mm, Delta H <= 1e-4 MPa, final KKT <= 1e-6, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        }
    }
    with open(PKG_175 / "M1_C6_R12_ANDERSON_M2_AUTHORIZATION.json", "w", encoding="utf-8") as f:
        json.dump(auth_175, f, indent=2)

    print("Package 174 and 175 built and manifests generated successfully!")


if __name__ == "__main__":
    build()
