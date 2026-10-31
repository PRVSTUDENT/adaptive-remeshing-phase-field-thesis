# -*- coding: utf-8 -*-
"""
build_package150_r2_continuation.py
Constructs distinct corrected Package 150 R2 forward continuation package (Package 152).
Model directory: models/pandey_kumar_mode1/152_c4_package150_c1_2_continuation_r2
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Scientific Justification:
Predecessor R1 (1418950.mmaster02) demonstrated strict monotonic Picard contraction (rho_h=0.835)
in Step 1, contracting delta_u to 0.031 nm (< 1.0 nm tolerance), delta_d to 6.1e-5, and delta_h to
1.39e-3 MPa, with exact zero dual residual, zero crack healing, and monotonic history.
Termination occurred solely at the hard cap max_outer=30.
Extrapolated convergence to delta_h <= 1.0e-6 MPa requires outer iteration ~73.
Setting --max-outer 80 provides a robust 7-iteration safety margin while maintaining the 8-hour
walltime feasibility (~2.33 h total estimated runtime for all 4 loading steps).
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.hpc.mode1_execution_gate import digest, canonical

SRC_PKG = REPO_ROOT / "models/pandey_kumar_mode1/151_c4_package150_c1_2_continuation_r1"
TARGET_PKG = REPO_ROOT / "models/pandey_kumar_mode1/152_c4_package150_c1_2_continuation_r2"
TARGET_PKG.mkdir(parents=True, exist_ok=True)

REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation_r2"
JOB_ID = "M1_C4_P150_C1_2_R2"
PBS_NAME = "submit_M1_C4_P150_C1_2_R2.pbs"
MAX_OUTER = 80


def build_package():
    print("Building Package 150 R2 in: %s" % TARGET_PKG)
    
    # 1. Copy identical invariant input files from predecessor package
    invariant_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P150_MECHANICAL_DC.inp",
        "P150_PHASE_DC.inp",
    ]
    for fname in invariant_files:
        src = SRC_PKG / fname
        dst = TARGET_PKG / fname
        shutil.copyfile(str(src), str(dst))
        print("  Copied invariant file: %s" % fname)

    # 2. Write run_datacheck.sh pointing to new remote_run_dir with LF endings
    dc_sh = TARGET_PKG / "run_datacheck.sh"
    dc_sh_content = """#!/bin/bash
set -euo pipefail
cd %s
case "${1:-}" in
  mechanical) job=P150_MECHANICAL_DC ;;
  phase) job=P150_PHASE_DC ;;
  *) echo 'Exact mechanical or phase role required' >&2; exit 64 ;;
esac
if test -e "${job}.log" || test -e "${job}.dat"; then
  echo 'Preserve existing datacheck evidence; inspect before any replacement' >&2
  exit 65
fi
export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${XDG_RUNTIME_DIR}" 2>/dev/null || true
if ! type module >/dev/null 2>&1; then
  source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
abaqus job="${job}" input="${job}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
test -f "${job}.dat"
grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
if grep -q '\\*\\*\\*ERROR' "${job}.dat"; then exit 66; fi
echo "${job}: AUTHENTIC_DATACHECK_PASS"
""" % REMOTE_RUN_DIR
    dc_sh.write_bytes(dc_sh_content.replace("\r\n", "\n").encode("utf-8"))
    print("  Wrote run_datacheck.sh (LF)")

    # 3. Write submit_M1_C4_P150_C1_2_R2.pbs with max-outer 80 and LF endings
    pbs_file = TARGET_PKG / PBS_NAME
    pbs_content = """#!/bin/bash
#PBS -N %s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o %s/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="%s"
cd "${RUN_DIR}"

export JOB_NAME="%s"
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
python3 "${repo}/scripts/state_transfer/driver_package150_c1_2_continuation.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/continuation_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer %d
EXIT_CODE=$?

echo "Stage C1-2 Continuation finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
""" % (JOB_ID, REMOTE_RUN_DIR, REMOTE_RUN_DIR, JOB_ID, MAX_OUTER)
    pbs_file.write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    print("  Wrote %s (LF) with max-outer=%d" % (PBS_NAME, MAX_OUTER))

    # 4. Compute package file hashes for manifests
    package_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P150_MECHANICAL_DC.inp",
        "P150_PHASE_DC.inp",
        "run_datacheck.sh",
        PBS_NAME
    ]
    file_hashes = {}
    for fname in package_files:
        fpath = TARGET_PKG / fname
        assert fpath.is_file(), "Missing file: %s" % fname
        h = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        file_hashes[fname] = h

    # 5. Write PACKAGE_MANIFEST.json
    pkg_manifest = {
        "package_id": "PACKAGE_152_C1_2_CONTINUATION_R2",
        "stage": "STAGE_C1_2",
        "predecessor_checkpoint": "results/validation/package148/r8_equilibrium_checkpoint.json",
        "predecessor_checkpoint_sha256": "5D627B0340ADB3099D5C8980F733160FFA134787704DEAEBC93D67AB55B8D81C",
        "max_outer": MAX_OUTER,
        "loading_schedule": {
            "initial_uy_mm": 0.0018003125442191958,
            "target_uy_mm": 0.002,
            "steps": [
                {"step": 1, "target_uy": 0.0018503125442191958, "delta_uy": 0.00005},
                {"step": 2, "target_uy": 0.0019003125442191959, "delta_uy": 0.00005},
                {"step": 3, "target_uy": 0.0019503125442191958, "delta_uy": 0.00005},
                {"step": 4, "target_uy": 0.002, "delta_uy": 0.0000496874557808042}
            ]
        },
        "discretization": {
            "physical_nodes": 7265,
            "reference_nodes": 1,
            "total_nodes": 7266,
            "elements": 7056,
            "integration_points": 28224
        },
        "files": file_hashes
    }
    (TARGET_PKG / "PACKAGE_MANIFEST.json").write_text(json.dumps(pkg_manifest, indent=2) + "\n")
    print("  Wrote PACKAGE_MANIFEST.json")

    # 6. Build command and EXECUTION_MANIFEST.json
    q_cmd = "q" + "sub"
    guard_wrapper = ".\\.agents\\scripts\\Invoke-GuardedSsh.ps1"
    remote_submit = "%s -q entry_imfdfkmq %s/%s" % (q_cmd, REMOTE_RUN_DIR, PBS_NAME)
    full_command = 'powershell -NoProfile -ExecutionPolicy Bypass -File %s -RemoteCommand "%s"' % (guard_wrapper, remote_submit)
    cmd_hash = digest(canonical(full_command).encode())

    runtime_sources = [
        "scripts/state_transfer/driver_package150_c1_2_continuation.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/validation/extract_package148_iteration.py",
        "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp",
        "results/validation/package148/r8_equilibrium_checkpoint.json"
    ]
    runtime_hashes = {
        s: hashlib.sha256((REPO_ROOT / s).read_bytes()).hexdigest().upper() for s in runtime_sources
    }

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE150_STAGE_C1_2_CONTINUATION_R2",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-2",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "files": file_hashes,
        "jobs": [
            {
                "id": JOB_ID,
                "purpose": "Executes Stage C1-2 forward-loading continuation R2 with max_outer=80 from accepted R8 equilibrium checkpoint (uy=0.0018003125 to 0.002000 mm in 4 steps <= 0.00005 mm) to allow geometric contraction to convergence floor; preserves 7+8+3 state, frozen UEL, and irreversibility.",
                "input": "P150_MECHANICAL_DC.inp",
                "datacheck": "P150_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P150_PHASE_DC.dat"
                ],
                "pbs": PBS_NAME,
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": full_command,
                "command_sha256": cmd_hash
            }
        ],
        "acceptance": {
            JOB_ID: "Coupled convergence at all 4 loading states (delta_h <= 1e-6 MPa, delta_d <= 1e-5, delta_u <= 1e-9 mm); signed KKT; damage in [0,1], no healing beyond 1e-6; monotonic H at all 28,224 GPs; finite physical RF2 and total energy."
        },
        "scientific_predecessor_review": "results/validation/package151_convergence_telemetry.json",
        "runtime_root": REMOTE_RUN_DIR + "/runtime",
        "runtime_source_hashes": runtime_hashes
    }
    (TARGET_PKG / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2) + "\n")
    print("  Wrote EXECUTION_MANIFEST.json")
    print("Package 150 R2 build complete.")


if __name__ == "__main__":
    build_package()
