#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart Candidate: M2STATE_FRACFIX_RESTART1R1R4.
Task ID: F46STATE-M2-FRACFIX-RESTART1R1R4-PREP-QUALIFY1

Revision Summary:
- Supersedes M2STATE_FRACFIX_RESTART1R1R3 (which failed Abaqus input processing due to INCPLICIT=YES keyword syntax typo).
- Corrects *STEP cards:
  * "*STEP, NAME=Step-1-PhaseInit, INCPLICIT=YES" -> "*STEP, NAME=Step-1-PhaseInit, INC=10000"
  * "*STEP, NAME=Step-2-Continuation, INCPLICIT=YES" -> "*STEP, NAME=Step-2-Continuation, INC=10000"
- Walltime updated: 04:00:00 -> 24:00:00 (resource envelope extension to avoid scheduler truncation).
- Integrates Dual-Channel Notification Policy (#PBS -m abe, #PBS -M pr21vyci@mailserver.tu-freiberg.de, job_notifications.sh, terminal traps).
- Preserves LF line endings (\n, CR_count = 0) across all scripts and execution files.
- Scientific formulation, topology (4894 physical elements, 9788 UELs), state-transfer numerical vectors, acceptance thresholds,
  UEL equations, trace representatives, and mechanical restart strategy remain 100% byte/logic identical to R1R1R3.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R3"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R4"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_lf_file(path: Path, text: str):
    """Write text file using strict LF line endings (\n) without CR (\r)."""
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(clean_text.encode("utf-8"))


def main():
    print("======================================================================")
    print("BUILDING CANDIDATE M2STATE_FRACFIX_RESTART1R1R4 (CORRECTED *STEP SYNTAX & LF)")
    print("======================================================================")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read source candidate files from R1R1R3
    r1r3_inp = (SRC_DIR / "M2STATE_FRACFIX_RESTART1R1R3.inp").read_text(encoding="utf-8")
    r1r3_uel = (SRC_DIR / "f42_mixed_uel.for").read_text(encoding="utf-8")
    r1r3_artifact = (SRC_DIR / "STATE_TRANSFER_ARTIFACT.json").read_text(encoding="utf-8")
    r1r3_transfer = (SRC_DIR / "TRANSFER_MANIFEST.json").read_text(encoding="utf-8")
    r1r3_contract = (SRC_DIR / "RESTART_ACCEPTANCE_CONTRACT.json").read_text(encoding="utf-8")
    r1r3_checker = (SRC_DIR / "verify_restart_trace.py").read_text(encoding="utf-8")

    # 1. Update candidate references from R1R1R3 to R1R1R4
    inp_code = r1r3_inp.replace("M2STATE_FRACFIX_RESTART1R1R3", "M2STATE_FRACFIX_RESTART1R1R4")
    uel_code = r1r3_uel.replace("M2STATE_FRACFIX_RESTART1R1R3", "M2STATE_FRACFIX_RESTART1R1R4")

    # 2. Correct *STEP keyword syntax typos
    assert "INCPLICIT=YES" in inp_code, "Expected INCPLICIT=YES in source deck"
    inp_code = inp_code.replace("*STEP, NAME=Step-1-PhaseInit, INCPLICIT=YES", "*STEP, NAME=Step-1-PhaseInit, INC=10000")
    inp_code = inp_code.replace("*STEP, NAME=Step-2-Continuation, INCPLICIT=YES", "*STEP, NAME=Step-2-Continuation, INC=10000")
    assert "INCPLICIT" not in inp_code, "INCPLICIT must not exist after correction!"

    artifact_dict = json.loads(r1r3_artifact)
    artifact_dict["target_job"] = "M2STATE_FRACFIX_RESTART1R1R4"
    artifact_str = json.dumps(artifact_dict, indent=2) + "\n"

    transfer_dict = json.loads(r1r3_transfer)
    transfer_dict["target_job"] = "M2STATE_FRACFIX_RESTART1R1R4"
    transfer_str = json.dumps(transfer_dict, indent=2) + "\n"

    contract_dict = json.loads(r1r3_contract)
    contract_dict["target_job"] = "M2STATE_FRACFIX_RESTART1R1R4"
    contract_str = json.dumps(contract_dict, indent=2) + "\n"

    checker_code = r1r3_checker.replace("M2STATE_FRACFIX_RESTART1R1R3", "M2STATE_FRACFIX_RESTART1R1R4")

    # Write target files
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R4.inp", inp_code)
    write_lf_file(OUT_DIR / "f42_mixed_uel.for", uel_code)
    write_lf_file(OUT_DIR / "STATE_TRANSFER_ARTIFACT.json", artifact_str)
    write_lf_file(OUT_DIR / "TRANSFER_MANIFEST.json", transfer_str)
    write_lf_file(OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", contract_str)
    write_lf_file(OUT_DIR / "verify_restart_trace.py", checker_code)

    # Write PBS Script with STRICT LF Line Endings & Mandatory Dual-Channel Notifications
    pbs_code = """#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R4
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART1R1R4.pbs.log

cd $PBS_O_WORKDIR

# Mandatory Dual-Channel Notification Integration
NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_SCRIPT="${NOTIFICATION_SCRIPT:-$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh}"

if [ -f "$NOTIFICATION_SCRIPT" ] && [ -f "$NOTIFICATION_CONFIG" ]; then
  source "$NOTIFICATION_SCRIPT" 2>/dev/null || true
  notification_load_config 2>/dev/null || true
  notification_install_terminal_trap 2>/dev/null || true
  notify_start 2>/dev/null || true
fi

echo "[PBS_PREFLIGHT] Starting M2STATE_FRACFIX_RESTART1R1R4 Production Restart Job..."
date

# Step 0: Package Hash Preflight Verification
python3 -c "
import json, hashlib, sys
from pathlib import Path

m = json.loads(Path('PACKAGE_MANIFEST.json').read_text())
for f, expected_hash in m['file_hashes'].items():
    p = Path(f)
    if not p.exists():
        print(f'[PBS_PREFLIGHT] ERROR: Missing file {f}')
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected_hash:
        print(f'[PBS_PREFLIGHT] ERROR: Hash mismatch for {f}: expected {expected_hash}, got {actual}')
        sys.exit(1)
print('[PBS_PREFLIGHT] PACKAGE HASHES VERIFIED 100% MATCH.')
"
if [ $? -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Package manifest verification failed."
  exit 1
fi

# Step 1: Purge and Load Qualified Modules
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_PREFLIGHT] Abaqus environment loaded."
abaqus information=release

# Step 2: Run Abaqus Execution Step
abaqus job=M2STATE_FRACFIX_RESTART1R1R4 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R4.inp interactive

ABAQUS_RC=$?
echo "[PBS_PREFLIGHT] Abaqus execution finished with exit code $ABAQUS_RC"

if [ $ABAQUS_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Abaqus execution failed with exit code $ABAQUS_RC"
  exit $ABAQUS_RC
fi

echo "[PBS_PREFLIGHT] Abaqus continuation step completed successfully."

# Step 3: Concatenate trace sinks and run checker
cat M2STATE_FRACFIX_RESTART1R1R4.dat M2STATE_FRACFIX_RESTART1R1R4.msg M2STATE_FRACFIX_RESTART1R1R4.log > M2STATE_FRACFIX_RESTART1R1R4.trace 2>/dev/null

python3 verify_restart_trace.py M2STATE_FRACFIX_RESTART1R1R4.trace
CHECKER_RC=$?

if [ $CHECKER_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Production restart trace checker failed with exit code $CHECKER_RC"
  exit $CHECKER_RC
fi

echo "[PBS_PREFLIGHT] ALL PRODUCTION RESTART CONTRACTS QUALIFIED SUCCESSFULLY."
"""
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R4.pbs", pbs_code)

    # Write Submit Wrapper with STRICT LF Line Endings & Mandatory Dual-Channel Notifications
    submit_code = """#!/bin/bash
# Guarded Submission Wrapper for M2STATE_FRACFIX_RESTART1R1R4
# Protocol: Standalone direct-human authorization required before direct qsub.

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
  DRY_RUN=true
fi

echo "[WRAPPER] Preflight verification for M2STATE_FRACFIX_RESTART1R1R4..."

MANIFEST="PACKAGE_MANIFEST.json"
if [ ! -f "$MANIFEST" ]; then
  echo "[WRAPPER] ERROR: $MANIFEST not found."
  exit 1
fi

python3 -c "
import json, hashlib, sys
from pathlib import Path

m = json.loads(Path('$MANIFEST').read_text())
for f, expected_hash in m['file_hashes'].items():
    p = Path(f)
    if not p.exists():
        print(f'[WRAPPER] ERROR: Missing package file {f}')
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected_hash:
        print(f'[WRAPPER] ERROR: Hash mismatch for {f}: expected {expected_hash}, got {actual}')
        sys.exit(1)
print('[WRAPPER] ALL PACKAGE FILE HASHES VERIFIED MATCH.')
"
if [ $? -ne 0 ]; then
  echo "[WRAPPER] ERROR: Package manifest hash verification failed."
  exit 1
fi

if [ "$DRY_RUN" = true ]; then
  echo "[WRAPPER] DRY-RUN COMPLETE: Preflight passed cleanly. qsub was NOT called."
  exit 0
fi

echo "[WRAPPER] FAIL-CLOSED: Direct qsub requires explicit human authorization."
exit 1
"""
    write_lf_file(OUT_DIR / "submit_m2state_fracfix_restart1r1r4.sh", submit_code)

    # Write PACKAGE_MANIFEST.json
    package_files = [
        "M2STATE_FRACFIX_RESTART1R1R4.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "verify_restart_trace.py",
        "M2STATE_FRACFIX_RESTART1R1R4.pbs",
        "submit_m2state_fracfix_restart1r1r4.sh"
    ]
    file_hashes = {f: sha256_file(OUT_DIR / f) for f in package_files}
    package_manifest = {
        "package_name": "M2STATE_FRACFIX_RESTART1R1R4",
        "protocol_version": 1,
        "task_id": "F46STATE-M2-FRACFIX-RESTART1R1R4-PREP-QUALIFY1",
        "execution_mode": "SERIAL",
        "cpus": 1,
        "memory_gb": 8,
        "walltime": "24:00:00",
        "file_hashes": file_hashes
    }
    manifest_str = json.dumps(package_manifest, indent=2) + "\n"
    write_lf_file(OUT_DIR / "PACKAGE_MANIFEST.json", manifest_str)
    print(f"Wrote PACKAGE_MANIFEST.json: {OUT_DIR / 'PACKAGE_MANIFEST.json'}")

    print("======================================================================")
    print("M2STATE_FRACFIX_RESTART1R1R4 PREPARATION COMPLETE")
    print("======================================================================")


if __name__ == "__main__":
    main()
