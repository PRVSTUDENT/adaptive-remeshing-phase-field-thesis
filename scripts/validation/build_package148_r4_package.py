#!/usr/bin/env python3
"""scripts/validation/build_package148_r4_package.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Builds and verifies Package 148 R4 immutable package directory and manifests:
- Preserves 7,056 elements, 7,265 nodes, active-set cards, and loading schedule.
- Binds R4 to the corrected driver (with 1e-8 ASCII .dat recovery tolerance).
- Preserves frozen production UEL: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
- Generates R4 PACKAGE_MANIFEST.json and EXECUTION_MANIFEST.json.
"""
from __future__ import print_function
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R3_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3"
R4_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r4"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r4"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def build_package_r4():
    R4_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy base static files from R3
    base_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C4_PACKAGE148_STATE_TRANSFER.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P148_MECHANICAL_DC.inp",
        "P148_PHASE_DC.inp",
    ]
    for fname in base_files:
        src = R3_DIR / fname
        dst = R4_DIR / fname
        shutil.copyfile(str(src), str(dst))

    # Verify UEL hash
    uel_hash = sha256_file(R4_DIR / "f42_mixed_uel.for").upper()
    assert uel_hash == FROZEN_UEL_SHA256, f"UEL hash mismatch: {uel_hash}"

    # 2. Create submit_M1_C4_P148_R4.pbs
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C4_P148_R4
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

export JOB_NAME="M1_C4_P148_R4"
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
python3 "${{repo}}/scripts/state_transfer/driver_package146_147_pdas_continuation.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/coupled_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --donor-rf2 0.1873079389333725 \\
    --donor-energy 0.00021270454000000001 \\
    --memory-gb 16
EXIT_CODE=$?

echo "Coupled PDAS finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (R4_DIR / "submit_M1_C4_P148_R4.pbs").write_text(pbs_content.replace("\r\n", "\n"), encoding="utf-8", newline="\n")

    # 3. Create run_datacheck.sh
    dc_content = f"""#!/bin/bash
set -euo pipefail
cd {REMOTE_RUN_DIR}
case "${{1:-}}" in
  mechanical) job=P148_MECHANICAL_DC ;;
  phase) job=P148_PHASE_DC ;;
  *) echo 'Exact mechanical or phase role required' >&2; exit 64 ;;
esac
if test -e "${{job}}.log" || test -e "${{job}}.dat"; then
  echo 'Preserve existing datacheck evidence; inspect before any replacement' >&2
  exit 65
fi
if ! type module >/dev/null 2>&1; then
  source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
abaqus job="${{job}}" input="${{job}}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${{job}}.stdout.txt" 2>&1
test -f "${{job}}.dat"
grep -q 'ANALYSIS DATACHECK COMPLETE' "${{job}}.dat"
if grep -q '\\*\\*\\*ERROR' "${{job}}.dat"; then exit 66; fi
echo "${{job}}: AUTHENTIC_DATACHECK_PASS"
"""
    (R4_DIR / "run_datacheck.sh").write_text(dc_content.replace("\r\n", "\n"), encoding="utf-8", newline="\n")

    # 4. Compute package file hashes (uppercase for PACKAGE_MANIFEST)
    pkg_files = {}
    for fname in sorted(base_files + ["submit_M1_C4_P148_R4.pbs"]):
        pkg_files[fname] = sha256_file(R4_DIR / fname).upper()

    # Load R3 manifest for base metadata
    r3_manifest = json.loads((R3_DIR / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))

    # Runtime source hashes in live repo
    runtime_source_hashes = {
        "scripts/state_transfer/build_package146_147_transfer_deck.py": sha256_file(REPO_ROOT / "scripts/state_transfer/build_package146_147_transfer_deck.py").upper(),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py").upper(),
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py").upper(),
        "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py").upper(),
    }

    # 5. Build PACKAGE_MANIFEST.json
    pkg_manifest = {
        "schema": 1,
        "history_gp_order": "MAPPER_ROW_FROM_UEL_PERIMETER",
        "runtime_source_hashes": runtime_source_hashes,
        "execution_status": "OFFLINE_CANDIDATE_REQUIRES_INDEPENDENT_RUNTIME_REVIEW",
        "derived_from": "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/PACKAGE_MANIFEST.json",
        "derived_from_sha256": sha256_file(R3_DIR / "PACKAGE_MANIFEST.json").upper(),
        "source_hashes": r3_manifest["source_hashes"],
        "package": 148,
        "revision": "R4",
        "model_name": "M1_C4_PACKAGE148_STATE_TRANSFER",
        "donor": r3_manifest["donor"],
        "receiver": r3_manifest["receiver"],
        "files": pkg_files,
        "frozen_uel_sha256": FROZEN_UEL_SHA256,
        "active_set_strategy": "ALTERNATING_PDAS_ACTIVE_SET_DECOUPLING",
        "correction_notes": "R4 corrects ASCII .dat node text extraction comparison tolerance from 1e-10 to 1e-8, eliminating spurious rejection from 8-digit float output truncation."
    }
    (R4_DIR / "PACKAGE_MANIFEST.json").write_text(json.dumps(pkg_manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 6. Build EXECUTION_MANIFEST.json (lowercase hashes)
    exec_files = {}
    for fname in sorted(base_files + ["PACKAGE_MANIFEST.json", "run_datacheck.sh", "submit_M1_C4_P148_R4.pbs"]):
        exec_files[fname] = sha256_file(R4_DIR / fname).lower()

    sub_cmd = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File '
        '.\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand '
        '"qsub -q entry_imfdfkmq ' + REMOTE_RUN_DIR + '/submit_M1_C4_P148_R4.pbs"'
    )
    cmd_hash = sha256_bytes(sub_cmd.encode('utf-8')).lower()

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE148_R4_STATE_TRANSFER",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "files": exec_files,
        "jobs": [
            {
                "id": "M1_C4_P148_R4",
                "purpose": "Reviewed genuine nonmatching state transfer with bounded alternating Abaqus mechanical/phase PDAS (R4 .dat text extraction tolerance repair to 1e-8); no continuation",
                "input": "P148_MECHANICAL_DC.inp",
                "datacheck": "P148_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P148_PHASE_DC.dat"
                ],
                "pbs": "submit_M1_C4_P148_R4.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": sub_cmd,
                "command_sha256": cmd_hash,
            }
        ],
        "acceptance": {
            "M1_C4_P148_R4": "Authentic coupled convergence and signed KKT; complete finite damage in [0,1], no healing beyond 1e-6; force jump <=5%, raw total energy jump <=2%; committed donor history preserved; no continuation until independent physical acceptance."
        },
        "scientific_predecessor_review": "results/validation/package148_r3_terminal_evaluation.json",
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": dict(r3_manifest["source_hashes"], **runtime_source_hashes)
    }
    (R4_DIR / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Package 148 R4 build complete.")


if __name__ == '__main__':
    build_package_r4()
