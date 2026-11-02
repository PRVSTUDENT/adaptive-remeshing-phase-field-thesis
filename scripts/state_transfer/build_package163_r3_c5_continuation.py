#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package163_r3_c5_continuation.py
Builds Package 163-R3 for Stage C2-1 (+5 nm C5 Forward Continuation with max_outer=300).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

R2_PKG = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r2_c2_1_continuation"
R3_PKG = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r3_c2_1_continuation"
CHECKPOINT_01_SRC = REPO_ROOT / "models/pandey_kumar_mode1/166_c5_package166_r3_c2_0_nonaccumulating_history/evidence/1419485.mmaster02/converged_checkpoint_01.json"

REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package163_r3_c2_1_continuation"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CHECKPOINT_01_SHA256 = "DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def canonical(cmd: str) -> str:
    return " ".join(cmd.strip().split())


def build():
    R3_PKG.mkdir(parents=True, exist_ok=True)

    # 1. Copy common state and deck files from Package 163-R2
    copy_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "f42_mixed_uel.for"
    ]
    for name in copy_files:
        src = R2_PKG / name
        dst = R3_PKG / name
        shutil.copyfile(src, dst)

    # Verify UEL
    uel_hash = sha256_file(R3_PKG / "f42_mixed_uel.for")
    assert uel_hash == FROZEN_UEL_SHA256, f"UEL hash mismatch: {uel_hash}"

    # Copy and verify authentic Checkpoint 01
    shutil.copyfile(CHECKPOINT_01_SRC, R3_PKG / "initial_checkpoint_01.json")
    chkpt_hash = sha256_file(R3_PKG / "initial_checkpoint_01.json")
    assert chkpt_hash == CHECKPOINT_01_SHA256, f"Checkpoint 01 hash mismatch: {chkpt_hash}"

    # 2. Input decks
    master_inp = R2_PKG / "M1_C5_PACKAGE163_R2_C2_1_CONTINUATION.inp"
    shutil.copyfile(master_inp, R3_PKG / "M1_C5_PACKAGE163_R3_C2_1_CONTINUATION.inp")

    # Datacheck decks
    shutil.copyfile(R2_PKG / "P163_R2_MECHANICAL_DC.inp", R3_PKG / "P163_R3_MECHANICAL_DC.inp")
    if not (R3_PKG / "P163_R3_MECHANICAL_DC.dat").exists():
        shutil.copyfile(R2_PKG / "P163_R2_MECHANICAL_DC.dat", R3_PKG / "P163_R3_MECHANICAL_DC.dat")
    shutil.copyfile(R2_PKG / "P163_R2_PHASE_DC.inp", R3_PKG / "P163_R3_PHASE_DC.inp")
    if not (R3_PKG / "P163_R3_PHASE_DC.dat").exists():
        shutil.copyfile(R2_PKG / "P163_R2_PHASE_DC.dat", R3_PKG / "P163_R3_PHASE_DC.dat")

    # 3. run_datacheck.sh
    run_dc_script = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_RUN_DIR}"

case "${{1:-}}" in
  mechanical) job=P163_R3_MECHANICAL_DC ;;
  phase) job=P163_R3_PHASE_DC ;;
  *) echo 'Exact mechanical or phase role required' >&2; exit 64 ;;
esac

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job="${{job}}" input="${{job}}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${{job}}.stdout.txt" 2>&1
test -f "${{job}}.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "${{job}}.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "${{job}}.dat"
if grep -q '\\*\\*\\*ERROR' "${{job}}.dat"; then exit 66; fi
echo "${{job}}: AUTHENTIC_DATACHECK_PASS"
"""
    (R3_PKG / "run_datacheck.sh").write_bytes(run_dc_script.replace("\r\n", "\n").encode("utf-8"))

    # 4. submit_M1_C5_P163_R3_C2_1.pbs
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C5_P163_R3_C2_1
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

export JOB_NAME="M1_C5_P163_R3_C2_1"
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
python3 "${{repo}}/scripts/state_transfer/driver_package163_r2_c5_continuation.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/continuation_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 300
EXIT_CODE=$?

echo "Stage C2-1 Forward Continuation finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (R3_PKG / "submit_M1_C5_P163_R3_C2_1.pbs").write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))

    # 5. Compute file hashes for PACKAGE_MANIFEST.json
    all_package_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_checkpoint_01.json",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C5_PACKAGE163_R3_C2_1_CONTINUATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P163_R3_MECHANICAL_DC.dat",
        "P163_R3_MECHANICAL_DC.inp",
        "P163_R3_PHASE_DC.dat",
        "P163_R3_PHASE_DC.inp",
        "run_datacheck.sh",
        "submit_M1_C5_P163_R3_C2_1.pbs"
    ]
    pkg_manifest_files = {}
    for name in sorted(all_package_files):
        p = R3_PKG / name
        assert p.is_file(), f"Missing file {name}"
        pkg_manifest_files[name] = sha256_file(p).lower()

    pkg_manifest = {
        "schema": 1,
        "package": "Package 163-R3 Stage C2-1 +5 nm Forward Continuation",
        "mesh": "Candidate C5 Mesh (12,996 quads, 13,278 nodes, 51,984 GPs)",
        "baseline_uy_mm": 0.0018603125442191958,
        "target_uy_mm": 0.0018653125442191958,
        "increment_nm": 5.0,
        "max_outer": 300,
        "predecessor_checkpoint_01_sha256": CHECKPOINT_01_SHA256,
        "files": pkg_manifest_files
    }
    (R3_PKG / "PACKAGE_MANIFEST.json").write_text(json.dumps(pkg_manifest, indent=2), encoding="utf-8")

    # Add PACKAGE_MANIFEST.json to files for EXECUTION_MANIFEST.json
    exec_manifest_files = dict(pkg_manifest_files)
    exec_manifest_files["PACKAGE_MANIFEST.json"] = sha256_file(R3_PKG / "PACKAGE_MANIFEST.json").lower()

    # 6. Runtime source hashes
    runtime_sources = {
        "scripts/state_transfer/driver_package163_r2_c5_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package163_r2_c5_continuation.py"),
        "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py"),
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py")
    }

    # Job command
    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_M1_C5_P163_R3_C2_1.pbs"'
    cmd_sha256 = hashlib.sha256(canonical(cmd).encode()).hexdigest()

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE163_R3_M1_C5_P163_R3_C2_1",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": runtime_sources,
        "files": exec_manifest_files,
        "scientific_predecessor_review": "results/validation/convergence_recovery_investigation_turn32.json",
        "jobs": [
            {
                "id": "M1_C5_P163_R3_C2_1",
                "purpose": "Mode-I Stage C2-1 +5 nm forward continuation on C5 receiver mesh with max_outer=300",
                "input": "P163_R3_MECHANICAL_DC.inp",
                "datacheck": "P163_R3_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P163_R3_PHASE_DC.dat"
                ],
                "pbs": "submit_M1_C5_P163_R3_C2_1.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": cmd,
                "command_sha256": cmd_sha256
            }
        ],
        "acceptance": {
            "M1_C5_P163_R3_C2_1": "Mode-I Stage C2-1 +5 nm forward continuation meeting coupled PDAS convergence (delta_d <= 1e-5, delta_u <= 1e-9 mm, delta_h <= 1e-4 MPa, force <= 2%, energy <= 2%) and physical acceptance with max_outer=300"
        }
    }
    (R3_PKG / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")
    print(f"Successfully generated Package 163-R3 in {R3_PKG}")
    print(f"Command SHA256: {cmd_sha256}")


if __name__ == "__main__":
    build()
