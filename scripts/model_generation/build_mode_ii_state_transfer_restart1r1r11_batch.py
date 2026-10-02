#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart-1 Candidate: M2STATE_FRACFIX_RESTART1R1R11.
Task ID: F95STATE-M2-INSTRUMENTED-RESTART1-R1R11-PREP-AND-QUALIFICATION1

Classification: INSTRUMENTED_RESTART1_EVIDENCE_RECOVERY_PREPARATION
Canonical Manifest Key: "files"

Key Features & Corrections:
1. Derived directly from validated M2STATE_FRACFIX_RESTART1R1R8 and instrumented R1R9/R1R10.
2. Adopts battle-tested robust PBS script structure from successful candidate R1R8 (Job 1389241.mmaster02):
   - PBS log redirection: #PBS -j oe, #PBS -o M2STATE_FRACFIX_RESTART1R1R11.pbs.log.
   - Dual-channel notifications: #PBS -m abe, #PBS -M pr21vyci@mailserver.tu-freiberg.de.
   - Robust environment initialization with fallback handling.
   - Correct notification helper invocation: notification_load_config.
3. Identical PK5 Target Mesh (4998 nodes, 4894 physical elements: 4766 quads, 128 tris).
4. Identical Clean 6-Slot Real Property ABI:
   PROPS(1) = E_L0 (0.015 mm)
   PROPS(2) = E_GC (0.0027 kN/mm)
   PROPS(3) = E_MOD (210.0 kN/mm^2)
   PROPS(4) = E_NU (0.3)
   PROPS(5) = E_K (1.0e-07)
   PROPS(6) = N_PHYS (4894.0)
5. Identical Safe Forward Jacobian & Matrix Inversion in f42_mixed_uel.for.
6. Identical Consistent Newton Phase Residual: RHS = F_H - K_phase * d for JTYPE 1 and JTYPE 3.
7. Identical Source Ingestion: Exclusively from valid predecessor job 1386469.mmaster02 at U1 = 0.005000 mm.
8. Identical Output Instrumentation:
   - *EL PRINT, FREQ=1, ELSET=E_MECH_UEL requesting SDV14, SDV15, SDV16 in .dat file.
   - *NODE OUTPUT, NSET=N_PHYSICAL (U), NSET=N_RP (U, RF), NSET=N_BOTTOM (U, RF).
   - *NODE PRINT, FREQ=1 (U, RF).
9. Preserves resource contract: 1 CPU, 16 GB, 24:00:00, entry_imfdfkmq.
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_R1R8_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8"
SRC_NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def write_lf_file(path: Path, text: str):
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(clean_text.encode("utf-8"))

def build_f42_mixed_uel_for() -> str:
    src_for = SRC_R1R8_DIR / "f42_mixed_uel.for"
    text = src_for.read_text(encoding="utf-8", errors="replace")
    text = text.replace("RESTART1R1R8", "RESTART1R1R11")
    return text

def generate_inp_deck() -> str:
    src_inp = SRC_R1R8_DIR / "M2STATE_FRACFIX_RESTART1R1R8.inp"
    text = src_inp.read_text(encoding="utf-8", errors="replace")
    text = text.replace("RESTART1R1R8", "RESTART1R1R11")

    # Add ELSET for all UEL elements if not present
    # Add N_RP node set and ELSETs
    rp_nset = """*NSET, NSET=N_RP
99999
*ELSET, ELSET=E_ALL_UEL
E_U1, E_U2, E_U3, E_U4
*ELSET, ELSET=E_MECH_UEL
E_U2, E_U4
*ELSET, ELSET=E_PHASE_UEL
E_U1, E_U3
"""
    # Insert N_RP and ELSETs before the first step
    step1_idx = text.find("*STEP, NAME=Step-1-PhaseInit")
    if step1_idx != -1:
        text = text[:step1_idx] + rp_nset + text[step1_idx:]

    # Instrument Step 1 output requests
    step1_old_output = """*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_PHYSICAL
U
*NODE PRINT, FREQ=1
U, RF
*END STEP"""

    step1_new_output = """*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_PHYSICAL
U
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*NODE PRINT, FREQ=1
U, RF
*EL PRINT, FREQ=1, ELSET=E_MECH_UEL
SDV14, SDV15, SDV16
*END STEP"""

    text = text.replace(step1_old_output, step1_new_output, 1)

    # Instrument Step 2 output requests
    step2_old_output = """*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_PHYSICAL
U
*NODE PRINT, FREQ=1
U, RF
*END STEP"""

    step2_new_output = """*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_PHYSICAL
U
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*NODE PRINT, FREQ=1
U, RF
*EL PRINT, FREQ=1, ELSET=E_MECH_UEL
SDV14, SDV15, SDV16
*END STEP"""

    text = text.replace(step2_old_output, step2_new_output, 1)

    return text


def generate_pbs_script() -> str:
    return """#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R11
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART1R1R11.pbs.log

cd "$PBS_O_WORKDIR"

# 1. Establish timing variables
JOB_START_EPOCH=$(date +%s)
echo "[PBS_PREFLIGHT] Starting M2STATE_FRACFIX_RESTART1R1R11 Production Restart Job..."
date

# 2. Source package-local notification helper and install terminal trap
NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_SCRIPT="${NOTIFICATION_SCRIPT:-${PBS_O_WORKDIR}/job_notifications.sh}"
if [ ! -f "$NOTIFICATION_SCRIPT" ]; then
  NOTIFICATION_SCRIPT="$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
fi

if [ -f "$NOTIFICATION_SCRIPT" ]; then
  source "$NOTIFICATION_SCRIPT" 2>/dev/null || true
  notification_load_config 2>/dev/null || true
  notification_install_terminal_trap 2>/dev/null || true
  notify_start 2>/dev/null || true
fi

# 3. Standalone manifest preflight
python3 validate_package_manifest.py PACKAGE_MANIFEST.json
PREFLIGHT_RC=$?

if [ $PREFLIGHT_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Package manifest verification failed with exit code $PREFLIGHT_RC"
  exit $PREFLIGHT_RC
fi

# 4. Load Abaqus environment
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_PREFLIGHT] Abaqus environment loaded."
abaqus information=release

# 5. Run solver
abaqus job=M2STATE_FRACFIX_RESTART1R1R11 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R11.inp interactive

ABAQUS_RC=$?
echo "[PBS_PREFLIGHT] Abaqus execution finished with exit code $ABAQUS_RC"

if [ $ABAQUS_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Abaqus execution failed with exit code $ABAQUS_RC"
  exit $ABAQUS_RC
fi

echo "[PBS_PREFLIGHT] M2STATE_FRACFIX_RESTART1R1R11 completed successfully."
exit 0
"""

def generate_submit_wrapper() -> str:
    return """#!/bin/bash
# Guarded Submission Wrapper for Candidate M2STATE_FRACFIX_RESTART1R1R11
# Max Submissions: 1 (Single Job Batch)
# Automatic Retry: FALSE

set -euo pipefail

CANDIDATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CANDIDATE_DIR"

echo "=== Preflight Verification for M2STATE_FRACFIX_RESTART1R1R11 ==="
python3 validate_package_manifest.py

DRY_RUN=false
if [ "${1:-}" == "--dry-run" ]; then
    DRY_RUN=true
    echo "[INFO] Dry run mode enabled. Submission wrapper verified without qsub."
    exit 0
fi

if [ "${1:-}" != "--execute" ]; then
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi

echo "=== Submitting Job M2STATE_FRACFIX_RESTART1R1R11 to PBS ==="
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART1R1R11.pbs)
echo "[SUBMISSION] Job submitted successfully: $JOB_ID"

if [ -f "$CANDIDATE_DIR/job_notifications.sh" ]; then
    source "$CANDIDATE_DIR/job_notifications.sh" 2>/dev/null || true
    notification_load_config 2>/dev/null || true
    notify_submitted "$JOB_ID" "M2STATE_FRACFIX_RESTART1R1R11" "entry_imfdfkmq" "1" "16gb" "24:00:00" 2>/dev/null || true
fi
"""

def generate_validator_script() -> str:
    return """#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    pkg_dir = Path(__file__).resolve().parent
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    for item in manifest["files"]:
        fname = item["filename"]
        expected_hash = item["sha256"]
        fpath = pkg_dir / fname
        if not fpath.exists():
            print("FAIL: Missing file %s" % fname)
            exit(1)
        actual_hash = sha256_file(fpath)
        if actual_hash != expected_hash:
            print("FAIL: Hash mismatch for %s: expected %s, got %s" % (fname, expected_hash, actual_hash))
            exit(1)
        print("PASS: %s -> %s" % (fname, actual_hash))
    print("ALL MANIFEST FILES VERIFIED PASS")

if __name__ == "__main__":
    main()
"""

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Building M2STATE_FRACFIX_RESTART1R1R11 in %s" % OUT_DIR)

    # 1. Fortran UEL
    for_text = build_f42_mixed_uel_for()
    write_lf_file(OUT_DIR / "f42_mixed_uel.for", for_text)

    # 2. Input deck
    inp_text = generate_inp_deck()
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R11.inp", inp_text)

    # 3. PBS script
    pbs_text = generate_pbs_script()
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R11.pbs", pbs_text)

    # 4. Submission wrapper
    sh_text = generate_submit_wrapper()
    write_lf_file(OUT_DIR / "submit_m2state_fracfix_restart1r1r11.sh", sh_text)
    os.chmod(OUT_DIR / "submit_m2state_fracfix_restart1r1r11.sh", 0o755)

    # 5. Validator
    val_text = generate_validator_script()
    write_lf_file(OUT_DIR / "validate_package_manifest.py", val_text)
    os.chmod(OUT_DIR / "validate_package_manifest.py", 0o755)

    # 6. Notifications
    notif_text = SRC_NOTIF_SH.read_text(encoding="utf-8", errors="replace")
    write_lf_file(OUT_DIR / "job_notifications.sh", notif_text)

    # 7. Metadata records
    state_artifact = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R11",
        "task_id": "F95STATE-M2-INSTRUMENTED-RESTART1-R1R11-PREP-AND-QUALIFICATION1",
        "predecessor_job": "1386469.mmaster02",
        "predecessor_candidate": "M2ADAPT_MM_FRACFIX_PROD",
        "checkpoint_u1_mm": 0.005000,
        "terminal_u1_mm": 0.010000,
        "target_mesh": "PK5",
        "n_phys": 4894,
        "n_nodes": 4998,
        "instrumentation": {
            "sdv_el_print": True,
            "sdv_history_slot": 16,
            "sdv_phase_slot": 14,
            "sdv_deg_slot": 15
        },
        "clean_6_slot_property_abi": True,
        "safe_jacobian_inversion": True,
        "pbs_structure": "ROBUST_R1R8_PATTERN"
    }
    write_lf_file(OUT_DIR / "STATE_TRANSFER_ARTIFACT.json", json.dumps(state_artifact, indent=2))

    transfer_manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R11",
        "source_checkpoint": "1386469.mmaster02",
        "phase_field_transferred": True,
        "history_field_transferred": True,
        "target_physical_elements": 4894,
        "layered_total_elements": 14682,
        "uel_types": ["U1", "U2", "U3", "U4"]
    }
    write_lf_file(OUT_DIR / "TRANSFER_MANIFEST.json", json.dumps(transfer_manifest, indent=2))

    restart_contract = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R11",
        "force_continuity_tolerance": 0.02,
        "phase_continuity_tolerance": 0.02,
        "global_equilibrium_tolerance_kN": 1.0e-5,
        "cutback_tolerance": 0,
        "nan_tolerance": 0
    }
    write_lf_file(OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", json.dumps(restart_contract, indent=2))

    # 8. Package Manifest
    files_to_hash = [
        "M2STATE_FRACFIX_RESTART1R1R11.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART1R1R11.pbs",
        "submit_m2state_fracfix_restart1r1r11.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json"
    ]

    manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R11",
        "protocol_version": 1,
        "task_id": "F95STATE-M2-INSTRUMENTED-RESTART1-R1R11-PREP-AND-QUALIFICATION1",
        "files": []
    }
    for f in sorted(files_to_hash):
        fpath = OUT_DIR / f
        h = sha256_file(fpath)
        manifest["files"].append({
            "filename": f,
            "sha256": h,
            "size_bytes": fpath.stat().st_size
        })

    manifest_json = json.dumps(manifest, indent=2)
    write_lf_file(OUT_DIR / "PACKAGE_MANIFEST.json", manifest_json)
    pkg_hash = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
    print("Package manifest generated with %d files, sealed hash: %s" % (len(manifest["files"]), pkg_hash))

if __name__ == "__main__":
    main()
