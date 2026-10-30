"""Prepare Package 148 R6 files, manifests, and staging."""
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R5_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r5"
R6_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6"


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def prepare_r6():
    R6_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy unchanged base files from R5
    base_files = [
        "M1_C4_PACKAGE148_STATE_TRANSFER.inp",
        "P148_MECHANICAL_DC.inp",
        "P148_PHASE_DC.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
    ]
    for bf in base_files:
        src = R5_DIR / bf
        dst = R6_DIR / bf
        shutil.copy2(src, dst)
        print(f"Copied {bf} -> {dst.name}")

    # 2. Write submit_M1_C4_P148_R6.pbs
    pbs_content = """#!/bin/bash
#PBS -N M1_C4_P148_R6
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r6/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r6"
cd "${RUN_DIR}"

export JOB_NAME="M1_C4_P148_R6"
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
python3 "${repo}/scripts/state_transfer/driver_package146_147_pdas_continuation.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/coupled_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --donor-rf2 0.1873079389333725 \\
    --donor-energy 0.00021270454000000001 \\
    --memory-gb 16 \\
    --timeout 7200 \\
    --max-outer 25
EXIT_CODE=$?

echo "Coupled PDAS finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    pbs_path = R6_DIR / "submit_M1_C4_P148_R6.pbs"
    pbs_path.write_text(pbs_content, encoding="utf-8")
    print("Created submit_M1_C4_P148_R6.pbs")

    # 3. Create PACKAGE_MANIFEST.json
    all_files_for_package_manifest = sorted(base_files + ["run_datacheck.sh", "submit_M1_C4_P148_R6.pbs"])
    pkg_manifest = {
        "batch_name": "MODE1_PACKAGE148_R6_STATE_TRANSFER",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "configuration": "MODE1_BASELINE",
        "files": {fname: sha256_file(R6_DIR / fname) for fname in all_files_for_package_manifest},
        "jobs": [
            {
                "id": "M1_C4_P148_R6",
                "purpose": "Corrected nonmatching state transfer coupled alternating PDAS (R6 driver timeout extended to 7200 s, max outer iterations 25, 7+8+3 solution card encoding)",
                "input": "P148_MECHANICAL_DC.inp",
                "datacheck": "P148_MECHANICAL_DC.dat",
                "additional_datachecks": ["P148_PHASE_DC.dat"],
                "pbs": "submit_M1_C4_P148_R6.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": []
            }
        ],
        "acceptance": {
            "M1_C4_P148_R6": "Authentic coupled convergence and signed KKT; complete finite damage in [0,1], no healing beyond 1e-6; force jump <=5%, raw total energy jump <=2%; committed donor history preserved; no continuation until independent physical acceptance."
        },
        "scientific_predecessor_review": "results/validation/package148_r5_terminal_evaluation.json"
    }
    pkg_manifest_path = R6_DIR / "PACKAGE_MANIFEST.json"
    pkg_manifest_path.write_text(json.dumps(pkg_manifest, indent=2), encoding="utf-8")
    print("Created PACKAGE_MANIFEST.json")

    # 4. Create EXECUTION_MANIFEST.json
    all_files_for_exec_manifest = sorted(all_files_for_package_manifest + ["PACKAGE_MANIFEST.json"])
    file_hashes = {fname: sha256_file(R6_DIR / fname) for fname in all_files_for_exec_manifest}

    remote_pbs_path = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r6/submit_M1_C4_P148_R6.pbs"
    command_str = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 '
        f'-RemoteCommand "qsub -q entry_imfdfkmq {remote_pbs_path}"'
    )
    cmd_hash = hashlib.sha256(command_str.encode("utf-8")).hexdigest().lower()

    runtime_source_files = [
        "models/pandey_kumar_mode1/146_c3_fine_donor/M1_C3_FINE_PACKAGE146_DONOR.inp",
        "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp",
        "tests/fixtures/package146147/146_step1_dat.txt.gz",
        "results/validation/package146147/evaluation.json",
        "scripts/state_transfer/build_package146_147_transfer_deck.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/validation/extract_package148_iteration.py",
    ]
    runtime_hashes = {
        rf: hashlib.sha256((REPO_ROOT / rf).read_bytes()).hexdigest().upper()
        for rf in runtime_source_files
    }

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE148_R6_STATE_TRANSFER",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r6",
        "files": file_hashes,
        "jobs": [
            {
                "id": "M1_C4_P148_R6",
                "purpose": "Reviewed genuine nonmatching state transfer with bounded alternating Abaqus mechanical/phase PDAS (R6 timeout extended to 7200 s, max_outer=25, 7+8+3 solution cards); no continuation",
                "input": "P148_MECHANICAL_DC.inp",
                "datacheck": "P148_MECHANICAL_DC.dat",
                "additional_datachecks": ["P148_PHASE_DC.dat"],
                "pbs": "submit_M1_C4_P148_R6.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": command_str,
                "command_sha256": cmd_hash
            }
        ],
        "acceptance": {
            "M1_C4_P148_R6": "Authentic coupled convergence and signed KKT; complete finite damage in [0,1], no healing beyond 1e-6; force jump <=5%, raw total energy jump <=2%; committed donor history preserved; no continuation until independent physical acceptance."
        },
        "scientific_predecessor_review": "results/validation/package148_r5_terminal_evaluation.json",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r6/runtime",
        "runtime_source_hashes": runtime_hashes
    }
    exec_manifest_path = R6_DIR / "EXECUTION_MANIFEST.json"
    exec_manifest_path.write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")
    print("Created EXECUTION_MANIFEST.json")
    print(f"Command SHA-256: {cmd_hash}")


if __name__ == "__main__":
    prepare_r6()
