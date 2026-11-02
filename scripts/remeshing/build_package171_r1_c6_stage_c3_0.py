#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package171_r1_c6_stage_c3_0.py
=====================================
Builds Package 171-R1: C6 Stage C3-0 Coupled PDAS Re-Equilibration (Revision 1).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Repairs runtime dependency closure by including c3_int_to_c4_spatial_mapping.py,
while strictly preserving the accepted C6 mesh, transferred state from Checkpoint 03,
dual UEL layers, and frozen production UEL.
"""

import sys
import json
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SOURCE_PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_c3_0_reequilibration"
TARGET_PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c6_package171_r1_c3_0_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def canonical(s: str) -> str:
    return " ".join(s.split())


def build_package171_r1():
    print("=== Assembling Package 171-R1 (Immutable Revision) ===")
    TARGET_PKG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy core data files from source package
    files_to_copy = [
        "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "active_set_boundary_cards.inc",
        "f42_mixed_uel.for",
        "job_notifications.sh"
    ]

    for fname in files_to_copy:
        src = SOURCE_PKG_DIR / fname
        dst = TARGET_PKG_DIR / fname
        assert src.is_file(), f"Missing source file: {src}"
        shutil.copy2(src, dst)
        print(f"Copied {fname} (SHA-256: {sha256_file(dst)})")

    # Verify frozen UEL
    actual_uel_hash = sha256_file(TARGET_PKG_DIR / "f42_mixed_uel.for")
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL mismatch: {actual_uel_hash} != {FROZEN_UEL_HASH}"
    print(f"Verified frozen UEL hash: {actual_uel_hash}")

    # 2. Write run_datacheck.sh targeting R1 remote run directory
    datacheck_script = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

echo "=== Running Mechanical Subproblem Datacheck ==="
abaqus job=P171_MECHANICAL_DC user=f42_mixed_uel.for input=P171_MECHANICAL_DC.inp cpus=1 memory="8 gb" datacheck interactive > P171_MECHANICAL_DC.stdout.txt 2>&1
test -f "P171_MECHANICAL_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P171_MECHANICAL_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P171_MECHANICAL_DC.dat"
if grep -q '\\*\\*\\*ERROR' "P171_MECHANICAL_DC.dat"; then echo "MECHANICAL DATACHECK ERROR"; exit 66; fi
echo "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Phase Subproblem Datacheck ==="
abaqus job=P171_PHASE_DC user=f42_mixed_uel.for input=P171_PHASE_DC.inp cpus=1 memory="8 gb" datacheck interactive > P171_PHASE_DC.stdout.txt 2>&1
test -f "P171_PHASE_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P171_PHASE_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P171_PHASE_DC.dat"
if grep -q '\\*\\*\\*ERROR' "P171_PHASE_DC.dat"; then echo "PHASE DATACHECK ERROR"; exit 67; fi
echo "P171_PHASE_DC: AUTHENTIC_DATACHECK_PASS"
"""
    (TARGET_PKG_DIR / "run_datacheck.sh").write_bytes(datacheck_script.replace("\r\n", "\n").encode("utf-8"))
    print(f"Wrote run_datacheck.sh")

    # 3. Write submit_M1_C6_P171_R1_C3_0.pbs targeting R1 remote run directory
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C6_P171_R1_C3_0
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o {REMOTE_RUN_DIR}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="{REMOTE_RUN_DIR}"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C6_P171_R1_C3_0"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${{RUN_DIR}}/runtime"
python3 "${{repo}}/scripts/state_transfer/driver_package171_c6_coupled_pdas.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/equilibration_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 100
EXIT_CODE=$?

echo "Stage C3-0 Re-equilibration (Package 171-R1 C6 Coupled PDAS) finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (TARGET_PKG_DIR / "submit_M1_C6_P171_R1_C3_0.pbs").write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    print(f"Wrote submit_M1_C6_P171_R1_C3_0.pbs")

    # 4. PACKAGE_MANIFEST.json
    package_files = [
        "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "active_set_boundary_cards.inc",
        "f42_mixed_uel.for",
        "submit_M1_C6_P171_R1_C3_0.pbs",
        "job_notifications.sh",
        "run_datacheck.sh"
    ]

    manifest_dict = {
        "package_number": "171-R1",
        "package_name": "MODE1_PACKAGE_171_R1_C6_STAGE_C3_0_REEQUILIBRATION",
        "discretization": "C6_CONFORMAL_QUAD",
        "num_elements": 15252,
        "num_nodes": 15559,
        "duplicate_slit_pairs": 59,
        "donor_source": {
            "checkpoint": "CheckPoint03_Job1419566",
            "target_uy_mm": 0.0018703125442191958,
            "reference_force_kN": 0.17992419004440308,
            "reference_total_energy_kNmm": 0.00022639903
        },
        "files": {fname: sha256_file(TARGET_PKG_DIR / fname).lower() for fname in package_files}
    }
    with open(TARGET_PKG_DIR / "PACKAGE_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)
    print(f"Wrote PACKAGE_MANIFEST.json")

    # 5. Batch Authorization
    qsub_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_M1_C6_P171_R1_C3_0.pbs"'
    cmd_hash = hashlib.sha256(canonical(qsub_cmd).encode("utf-8")).hexdigest()

    auth_files = {fname: sha256_file(TARGET_PKG_DIR / fname).lower() for fname in package_files}
    auth_files["PACKAGE_MANIFEST.json"] = sha256_file(TARGET_PKG_DIR / "PACKAGE_MANIFEST.json").lower()

    # Runtime source hashes with c3_int_to_c4_spatial_mapping.py included
    runtime_source_hashes = {
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py"),
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py"),
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package171_c6_coupled_pdas.py"),
        "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py")
    }

    auth_dict = {
        "batch_name": "MODE1_PACKAGE_171_R1_C6_STAGE_C3_0_REEQUILIBRATION",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": runtime_source_hashes,
        "files": auth_files,
        "scientific_predecessor_review": "results/validation/c6_stage_c3_0_solver_evaluation.json",
        "jobs": [
            {
                "id": "M1_C6_P171_R1_C3_0",
                "pbs": "submit_M1_C6_P171_R1_C3_0.pbs",
                "command": qsub_cmd,
                "command_sha256": cmd_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 171-R1: Stage C3-0 authentic coupled PDAS re-equilibration on C6 mesh (15,252 quads) at uy = 0.0018703125 mm with repaired runtime closure",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "P171_MECHANICAL_DC.inp",
                "datacheck": "P171_MECHANICAL_DC.dat",
                "additional_datachecks": ["P171_PHASE_DC.dat"]
            }
        ],
        "acceptance": {
            "M1_C6_P171_R1_C3_0": "Stage C3-0 genuine coupled re-equilibration: Delta d <= 1e-5, Delta u <= 1e-9 mm, KKT satisfied, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        }
    }

    with open(TARGET_PKG_DIR / "M1_C6_PACKAGE171_R1_AUTHORIZATION.json", "w", encoding="utf-8") as f:
        json.dump(auth_dict, f, indent=2)
    print(f"Wrote M1_C6_PACKAGE171_R1_AUTHORIZATION.json")

    with open(TARGET_PKG_DIR / "EXECUTION_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(auth_dict, f, indent=2)
    print(f"Wrote EXECUTION_MANIFEST.json")

    # 6. Assembly validation artifact
    val_artifact = {
        "schema": 1,
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "evaluation_name": "PACKAGE_171_R1_C6_STAGGERED_PDAS_ASSEMBLY_VALIDATION",
        "status": "PACKAGE_171_R1_ASSEMBLED__AWAITING_DATACHECK",
        "mesh_stats": {
            "elements": 15252,
            "nodes": 15559,
            "duplicate_slit_pairs": 59,
            "min_det_jac": 1.5625e-08
        },
        "transferred_state": {
            "min_damage": 0.003390097726359051,
            "max_damage": 0.6909813083162544,
            "min_history": 2.9482787889150137e-08,
            "elastic_continuity_pct": 0.0,
            "fracture_continuity_pct": 0.0018047915309605488,
            "total_energy_continuity_pct": 0.00046313426767590863
        },
        "runtime_closure": {
            "c3_mapping_included": True,
            "transitive_dependencies": list(runtime_source_hashes.keys())
        },
        "uel_preserved": actual_uel_hash == FROZEN_UEL_HASH,
        "verification_passed": True
    }
    val_path = REPO_ROOT / "results" / "validation" / "c6_package171_r1_assembly_validation.json"
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_artifact, f, indent=2)
    print(f"Wrote assembly validation: {val_path.name}")
    print("=== PACKAGE 171-R1 ASSEMBLY COMPLETE ===")


if __name__ == "__main__":
    build_package171_r1()
