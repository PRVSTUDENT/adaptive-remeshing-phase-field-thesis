#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_package171_r11.py
==========================
Assembles Package 171-R11 (C6 Coupled PDAS Re-Equilibration Revision 11 - Safeguarded
Limited-Memory Anderson Acceleration) locally under:
models/pandey_kumar_mode1/171_c6_package171_r11_c3_0_adaptive_reequilibration.

Performs:
1. Copies invariant mesh, transfer state, boundary decks, and datacheck inputs from R10.
2. Strictly verifies bitwise SHA-256 match of frozen production UEL.
3. Generates M1_C6_PACKAGE171_R11_C3_0_ADAPTIVE_REEQUILIBRATION.inp.
4. Generates submit_M1_C6_P171_R11_C3_0.pbs referencing driver_package171_r11_c6_coupled_pdas.py
   and safeguarded Anderson acceleration CLI parameters.
5. Generates smoke_import.py exercising Anderson accelerator and R11 driver imports.
6. Generates M1_C6_PACKAGE171_R11_AUTHORIZATION.json (max_submissions: 0 under Task F1618).
7. Computes and writes PACKAGE_MANIFEST.json with SHA-256 hashes for all package files.
8. Generates EXECUTION_MANIFEST.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R10_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r10_c3_0_adaptive_reequilibration"
R11_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r11_c3_0_adaptive_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def assemble_r11():
    print("=== Assembling Package 171-R11 Locally ===")
    R11_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Invariant transfer and mesh files to copy from R10
    invariant_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "run_datacheck.sh",
    ]

    for fname in invariant_files:
        src = R10_DIR / fname
        dst = R11_DIR / fname
        shutil.copy2(src, dst)
        print(f"Copied invariant file: {fname}")

    # 2. Verify frozen UEL
    uel_hash = sha256_file(R11_DIR / "f42_mixed_uel.for")
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_hash} != {FROZEN_UEL_HASH}"
    print(f"Verified frozen production UEL: {uel_hash}")

    # 3. Create R11 main input deck
    r10_inp = R10_DIR / "M1_C6_PACKAGE171_R10_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
    r11_inp = R11_DIR / "M1_C6_PACKAGE171_R11_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
    inp_content = r10_inp.read_text(encoding="utf-8")
    inp_content = inp_content.replace("M1_C6_PACKAGE171_R10", "M1_C6_PACKAGE171_R11")
    inp_content = inp_content.replace("Revision 10", "Revision 11 - Anderson Acceleration")
    r11_inp.write_text(inp_content, encoding="utf-8")
    print(f"Generated R11 input deck: {r11_inp.name}")

    # 4. Generate submit_M1_C6_P171_R11_C3_0.pbs
    pbs_content = """#!/bin/bash
#PBS -N M1_C6_P171_R11_C3_0
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c6_package171_r11_c3_0_adaptive_reequilibration/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c6_package171_r11_c3_0_adaptive_reequilibration"
cd "${RUN_DIR}"

export JOB_NAME="M1_C6_P171_R11_C3_0"
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
python3 "${repo}/scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py" \\
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
    --anderson-enabled \\
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

echo "Stage C3-0 Re-equilibration (Package 171-R11 C6 Coupled PDAS with Safeguarded Anderson Acceleration) finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    r11_pbs = R11_DIR / "submit_M1_C6_P171_R11_C3_0.pbs"
    r11_pbs.write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    print(f"Generated R11 submit PBS script: {r11_pbs.name}")

    # 5. Generate smoke_import.py
    smoke_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"Remote import smoke test for Package 171-R11.\"\"\"
import sys
from pathlib import Path

cur_dir = Path(__file__).resolve().parent
repo = cur_dir / "runtime"
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

try:
    import scripts.state_transfer.anderson_acceleration as anderson
    assert hasattr(anderson, "AndersonAccelerator"), "Anderson class missing"
    import scripts.state_transfer.driver_package171_r11_c6_coupled_pdas as p171_r11
    assert hasattr(p171_r11, "Package171R11C6PDASDriver"), "Driver class missing"
    assert hasattr(p171_r11, "DONOR_REFERENCE_FORCE_KN"), "Reference constants missing"
    print("REMOTE_IMPORT_SUCCESS: True")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    r11_smoke = R11_DIR / "smoke_import.py"
    r11_smoke.write_bytes(smoke_content.replace("\r\n", "\n").encode("utf-8"))
    print(f"Generated R11 smoke import test: {r11_smoke.name}")

    # 6. Generate M1_C6_PACKAGE171_R11_AUTHORIZATION.json
    driver_r11_path = REPO_ROOT / "scripts" / "state_transfer" / "driver_package171_r11_c6_coupled_pdas.py"
    anderson_path = REPO_ROOT / "scripts" / "state_transfer" / "anderson_acceleration.py"
    extract_path = REPO_ROOT / "scripts" / "validation" / "extract_package148_iteration.py"
    auth_data = {
        "batch_name": "MODE1_PACKAGE_171_R11_C6_STAGE_C3_0_ADAPTIVE_REEQUILIBRATION",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 0,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c6_package171_r11_c3_0_adaptive_reequilibration",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c6_package171_r11_c3_0_adaptive_reequilibration/runtime",
        "governance_note": "Task F1618 authorizes staging and Abaqus datachecks only. Strictly 0 production solver PBS submissions authorized.",
        "runtime_source_hashes": {
            "scripts/state_transfer/anderson_acceleration.py": sha256_file(anderson_path),
            "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts" / "state_transfer" / "c3_int_to_c4_spatial_mapping.py"),
            "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts" / "state_transfer" / "c4_to_c5_spatial_mapping.py"),
            "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts" / "state_transfer" / "driver_package146_147_pdas_continuation.py"),
            "scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py": sha256_file(driver_r11_path),
            "scripts/validation/extract_package148_iteration.py": sha256_file(extract_path),
        },
        "files": {},
        "scientific_predecessor_review": "Independent review APPROVE decision under correlation HND-28c27a010ce8 (protocol INDEPENDENT_STRUCTURED_RE_REVIEW_V4) at commit b7df3e50 closing F1617",
        "jobs": [
            {
                "id": "M1_C6_P171_R11_C3_0",
                "pbs": "submit_M1_C6_P171_R11_C3_0.pbs",
                "command": 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c6_package171_r11_c3_0_adaptive_reequilibration/submit_M1_C6_P171_R11_C3_0.pbs"',
                "max_submissions": 0,
                "depends_on": [],
                "purpose": "Package 171-R11: Stage C3-0 authentic coupled PDAS re-equilibration on C6 mesh (15,252 quads) at uy = 0.0018703125 mm with two-phase safeguarded relaxation (Stage 1 omega_d = 0.50, omega_u = 1.00; Stage 2 omega_d = 0.85, omega_u = 0.85) and safeguarded limited-memory Anderson acceleration (m=2, beta=0.85, reg=1e-6, gamma_max=200, step_cap=0.045), raw damage residual false-convergence safeguard, and independent post-convergence re-equilibration gate",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "P171_MECHANICAL_DC.inp",
                "datacheck": "P171_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P171_PHASE_DC.dat"
                ]
            }
        ],
        "acceptance": {
            "M1_C6_P171_R11_C3_0": "Stage C3-0 genuine coupled re-equilibration (R11): Delta d <= 1e-5, raw Delta d <= 1e-5, raw Delta u <= 1e-9 mm, relaxed Delta u <= 1e-9 mm, Delta H <= 1e-4 MPa, independent re-equilibration Delta u <= 1e-9 mm, Delta H <= 1e-4 MPa, final KKT <= 1e-6, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        }
    }

    # 7. Generate PACKAGE_MANIFEST.json
    manifest = {
        "schema": 1,
        "package_name": "package171_r11_c6_c3_0_adaptive_reequilibration",
        "description": "Package 171-R11 C6 Coupled PDAS Re-Equilibration with Two-Phase Adaptive Relaxation, Isolated Displacement Under-Relaxation (omega_u=0.85 in Stage 2), Safeguarded Limited-Memory Anderson Acceleration (m=2, beta=0.85, step_cap=0.045), and Raw Damage Fixed-Point False Convergence Safeguard",
        "frozen_uel_sha256": FROZEN_UEL_HASH,
        "donor_source": {
            "checkpoint": "Checkpoint 03 (Job 1419566.mmaster02)",
            "target_uy_mm": 0.0018703125442191958,
            "donor_reference_force_kN": 0.17992419004440308,
            "donor_reference_total_energy_kNmm": 0.00022639903,
        },
        "receiver_mesh": {
            "name": "C6_Receiver",
            "elements_quad": 15252,
            "physical_nodes": 15559,
            "slit_pairs": 59,
        },
        "numerical_parameters": {
            "damping_omega_d_stage1": 0.50,
            "damping_omega_d_stage2": 0.85,
            "damping_omega_u_stage1": 1.00,
            "damping_omega_u_stage2": 0.85,
            "anderson_enabled": True,
            "anderson_memory": 2,
            "anderson_beta": 0.85,
            "anderson_reg": 1e-6,
            "anderson_gamma_max": 200.0,
            "anderson_max_step_cap": 0.045,
            "max_active_cardinality": 500,
            "max_symmetric_diff": 10,
            "max_added_nodes": 0,
            "stabilization_window": 3,
            "rollback_factor": 1.05,
            "divergence_factor": 1.50,
            "catastrophic_delta_d_cap": 0.05,
            "max_outer_iterations": 140,
            "delta_d_tol": 1e-05,
            "delta_u_tol_mm": 1e-09,
            "delta_h_tol_MPa": 0.0001,
            "consistency_delta_u_tol_mm": 1e-09,
            "consistency_delta_h_tol_MPa": 0.0001,
            "kkt_tol": 1e-06,
        },
        "files": {},
    }

    # Add file hashes to manifest and auth_data
    for f in sorted(R11_DIR.iterdir()):
        if f.is_file() and f.name not in ("PACKAGE_MANIFEST.json", "M1_C6_PACKAGE171_R11_AUTHORIZATION.json", "EXECUTION_MANIFEST.json"):
            f_hash = sha256_file(f)
            manifest["files"][f.name] = {
                "sha256": f_hash,
                "size_bytes": f.stat().st_size,
            }
            auth_data["files"][f.name] = f_hash.lower()

    # Write auth json
    auth_path = R11_DIR / "M1_C6_PACKAGE171_R11_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)
    print(f"Generated authorization file: {auth_path.name}")

    # Add auth file itself to manifest
    manifest["files"][auth_path.name] = {
        "sha256": sha256_file(auth_path),
        "size_bytes": auth_path.stat().st_size,
    }

    # Write manifest
    manifest_path = R11_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated PACKAGE_MANIFEST.json with {len(manifest['files'])} registered files.")

    # Write execution manifest
    exec_manifest = {
        "package_id": "mode1_c6_package171_r11_c3_0_adaptive_reequilibration",
        "authorization": "M1_C6_PACKAGE171_R11_AUTHORIZATION.json",
        "package_manifest": "PACKAGE_MANIFEST.json",
        "manifest_sha256": sha256_file(manifest_path),
        "auth_sha256": sha256_file(auth_path),
        "files_count": len(manifest["files"]) + 1,
    }
    exec_manifest_path = R11_DIR / "EXECUTION_MANIFEST.json"
    with open(exec_manifest_path, "w", encoding="utf-8") as f:
        json.dump(exec_manifest, f, indent=2)
    print(f"Generated EXECUTION_MANIFEST.json.")

    print("\n=== Package 171-R11 Local Assembly Complete ===")


if __name__ == "__main__":
    assemble_r11()
