#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package171_r6_manifests.py
=================================
Builds the Package 171-R6 package directory, PBS script, PACKAGE_MANIFEST.json,
M1_C6_PACKAGE171_R6_AUTHORIZATION.json, and EXECUTION_MANIFEST.json with exact SHA-256 hashes.
"""

import sys
import shutil
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

R5_PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration"
R6_PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r6_c3_0_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_lower(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().lower()


def sha256_upper(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def main():
    R6_PKG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy immutable model files from R5 (preserving mesh, CSVs, datachecks, UEL)
    copy_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P171_MECHANICAL_DC.dat",
        "P171_MECHANICAL_DC.inp",
        "P171_MECHANICAL_DC.msg",
        "P171_PHASE_DC.dat",
        "P171_PHASE_DC.inp",
        "P171_PHASE_DC.msg",
        "run_datacheck.sh",
        "smoke_import.py"
    ]
    for fname in copy_files:
        src = R5_PKG_DIR / fname
        dst = R6_PKG_DIR / fname
        shutil.copy2(src, dst)

    # Verify frozen UEL bitwise identity
    uel_hash = sha256_upper(R6_PKG_DIR / "f42_mixed_uel.for")
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: expected {FROZEN_UEL_HASH}, got {uel_hash}"

    # 2. Write submit_M1_C6_P171_R6_C3_0.pbs
    pbs_content = """#!/bin/bash
#PBS -N M1_C6_P171_R6_C3_0
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c6_package171_r6_c3_0_reequilibration/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c6_package171_r6_c3_0_reequilibration"
cd "${RUN_DIR}"

export JOB_NAME="M1_C6_P171_R6_C3_0"
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
python3 "${repo}/scripts/state_transfer/driver_package171_r6_c6_coupled_pdas.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/equilibration_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 100 \\
    --damping-omega-d 0.5
EXIT_CODE=$?

echo "Stage C3-0 Re-equilibration (Package 171-R6 C6 Coupled PDAS Fail-Closed Phase Decoding omega_d = 0.5) finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    (R6_PKG_DIR / "submit_M1_C6_P171_R6_C3_0.pbs").write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))

    # 3. Hash files for PACKAGE_MANIFEST.json
    pkg_files = {}
    for p in sorted(R6_PKG_DIR.iterdir()):
        if p.is_file() and p.name not in (
            "PACKAGE_MANIFEST.json",
            "EXECUTION_MANIFEST.json",
            "M1_C6_PACKAGE171_R6_AUTHORIZATION.json"
        ):
            pkg_files[p.name] = sha256_lower(p)

    manifest_data = {
        "package_name": "mode1_c6_package171_r6_c3_0_reequilibration",
        "protocol_version": 2,
        "description": "Package 171-R6: Mode-I C6 Stage C3-0 genuine coupled PDAS re-equilibration with fail-closed phase-field decoding validating 15,559 physical nodes and rejecting 2-component/mixed output (omega_d = 0.5)",
        "donor_source": {
            "checkpoint": "Checkpoint 03 (Job 1419566.mmaster02)",
            "target_uy_mm": 0.0018703125442191958,
            "donor_reference_force_kN": 0.17992419004440308,
            "donor_reference_total_energy_kNmm": 0.00022639903
        },
        "receiver_mesh": {
            "name": "C6_Receiver",
            "elements_quad": 15252,
            "physical_nodes": 15559,
            "slit_pairs": 59
        },
        "numerical_parameters": {
            "damping_omega_d": 0.5,
            "max_outer_iterations": 100,
            "delta_d_tol": 1.0e-5,
            "delta_u_tol_mm": 1.0e-9,
            "delta_h_tol_MPa": 1.0e-4,
            "consistency_delta_u_tol_mm": 1.0e-9,
            "consistency_delta_h_tol_MPa": 1.0e-4,
            "kkt_tol": 1.0e-6
        },
        "remediation_status": {
            "defect_phase_decoding": "RESOLVED_FAIL_CLOSED_15559_NODES_REJECT_2COMP_MIXED",
            "defect_1_gauss_point_history_loading": "PRESERVED_4_GP_DISTINCT",
            "defect_2_split_keyword_blocks_unpacking": "PRESERVED_STRING_BLOCK_PARSING",
            "defect_3_uel_solution_state_formatting": "PRESERVED_ELEMENT_LEVEL_INITIAL_CONDITIONS",
            "defect_4_odb_extractor_cli_args": "PRESERVED_PHYSICAL_NODES_ELEMENTS_STEP",
            "defect_5_displacement_consistency_gate": "PRESERVED_STRICT_1E-9_MM",
            "defect_6_history_consistency_gate": "PRESERVED_STRICT_1E-4_MPA",
            "defect_7_final_kkt_stationarity_gate": "PRESERVED_STRICT_1E-6",
            "defect_8_gated_checkpoint_commitment": "PRESERVED_PHYSICAL_PASS_CONDITIONAL"
        },
        "files": pkg_files
    }
    manifest_path = R6_PKG_DIR / "PACKAGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    pkg_files["PACKAGE_MANIFEST.json"] = sha256_lower(manifest_path)

    # 4. Runtime source dependencies
    runtime_sources = {
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": sha256_upper(REPO_ROOT / "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py"),
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_upper(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_upper(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py"),
        "scripts/state_transfer/driver_package171_r6_c6_coupled_pdas.py": sha256_upper(REPO_ROOT / "scripts/state_transfer/driver_package171_r6_c6_coupled_pdas.py"),
        "scripts/validation/extract_package148_iteration.py": sha256_upper(REPO_ROOT / "scripts/validation/extract_package148_iteration.py")
    }

    # 5. Write M1_C6_PACKAGE171_R6_AUTHORIZATION.json
    pbs_cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c6_package171_r6_c3_0_reequilibration/submit_M1_C6_P171_R6_C3_0.pbs"'
    cmd_sha256 = hashlib.sha256(pbs_cmd.encode("utf-8")).hexdigest().lower()

    auth_data = {
        "batch_name": "MODE1_PACKAGE_171_R6_C6_STAGE_C3_0_REEQUILIBRATION",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c6_package171_r6_c3_0_reequilibration",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c6_package171_r6_c3_0_reequilibration/runtime",
        "runtime_source_hashes": runtime_sources,
        "files": pkg_files,
        "scientific_predecessor_review": "results/validation/c6_r6_independent_review_remediation_analysis.json",
        "jobs": [
            {
                "id": "M1_C6_P171_R6_C3_0",
                "pbs": "submit_M1_C6_P171_R6_C3_0.pbs",
                "command": pbs_cmd,
                "command_sha256": cmd_sha256,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 171-R6: Stage C3-0 authentic coupled PDAS re-equilibration on C6 mesh (15,252 quads) at uy = 0.0018703125 mm with fail-closed phase decoding (15,559 nodes, rejection of 2-component/mixed output), displacement consistency (<= 1e-9 mm), history consistency (<= 1e-4 MPa), and gated checkpointing (omega_d = 0.5)",
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
            "M1_C6_P171_R6_C3_0": "Stage C3-0 genuine coupled re-equilibration (R6): Delta d <= 1e-5, Delta u <= 1e-9 mm, Delta H <= 1e-4 MPa, consistency Delta u <= 1e-9 mm, consistency Delta H <= 1e-4 MPa, final KKT <= 1e-6, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        }
    }
    auth_path = R6_PKG_DIR / "M1_C6_PACKAGE171_R6_AUTHORIZATION.json"
    auth_path.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")

    # 6. Write EXECUTION_MANIFEST.json
    exec_manifest = {
        "package_id": "mode1_c6_package171_r6_c3_0_reequilibration",
        "authorization": "M1_C6_PACKAGE171_R6_AUTHORIZATION.json",
        "package_manifest": "PACKAGE_MANIFEST.json",
        "manifest_sha256": sha256_upper(manifest_path),
        "auth_sha256": sha256_upper(auth_path),
        "files_count": len(pkg_files)
    }
    (R6_PKG_DIR / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")

    print(f"Package 171-R6 manifests successfully generated in {R6_PKG_DIR}:")
    print(f"  PACKAGE_MANIFEST.json: {exec_manifest['manifest_sha256']}")
    print(f"  M1_C6_PACKAGE171_R6_AUTHORIZATION.json: {exec_manifest['auth_sha256']}")


if __name__ == "__main__":
    main()
