#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart-1 Candidate: M2STATE_FRACFIX_RESTART1R1R10.
Task ID: F93RECOVER-M2-INSTRUMENTED-RESTART1-R1R10-TECHNICAL-REPLACEMENT1

Classification: INSTRUMENTED_RESTART1_EVIDENCE_RECOVERY_TECHNICAL_REPLACEMENT
Canonical Manifest Key: "files"

Key Features & Corrections:
1. Derived directly from M2STATE_FRACFIX_RESTART1R1R9.
2. Fixes technical notification function invocation:
   load_notification_config -> notification_load_config (matching job_notifications.sh contract).
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
SRC_R1R9_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9"
SRC_NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R10"

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
    src_for = SRC_R1R9_DIR / "f42_mixed_uel.for"
    text = src_for.read_text(encoding="utf-8", errors="replace")
    text = text.replace("RESTART1R1R9", "RESTART1R1R10")
    return text

def generate_inp_deck() -> str:
    src_inp = SRC_R1R9_DIR / "M2STATE_FRACFIX_RESTART1R1R9.inp"
    text = src_inp.read_text(encoding="utf-8", errors="replace")
    text = text.replace("RESTART1R1R9", "RESTART1R1R10")
    return text

def generate_pbs_script() -> str:
    return """#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R10
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail

CANDIDATE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R10"
cd "$PBS_O_WORKDIR"

if [ -f "$CANDIDATE_DIR/job_notifications.sh" ]; then
    source "$CANDIDATE_DIR/job_notifications.sh"
    notification_load_config
    notify_start "$PBS_JOBID" "M2STATE_FRACFIX_RESTART1R1R10" "mnode" "entry_imfdfkmq" "24:00:00"
    notification_install_terminal_trap "$PBS_JOBID" "M2STATE_FRACFIX_RESTART1R1R10"
fi

source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_JOB] Job ID: $PBS_JOBID"
echo "[PBS_JOB] Host: $(hostname)"
echo "[PBS_JOB] Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

JOB_NAME="M2STATE_FRACFIX_RESTART1R1R10"
abaqus job="$JOB_NAME" user=f42_mixed_uel.for input="$JOB_NAME.inp" interactive

EXIT_CODE=$?
echo "[PBS_JOB] Abaqus finished with exit code: $EXIT_CODE"
exit $EXIT_CODE
"""

def generate_submit_wrapper() -> str:
    return """#!/bin/bash
# Guarded Submission Wrapper for Candidate M2STATE_FRACFIX_RESTART1R1R10
# Max Submissions: 1 (Single Job Batch)
# Automatic Retry: FALSE

set -euo pipefail

CANDIDATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CANDIDATE_DIR"

echo "=== Preflight Verification for M2STATE_FRACFIX_RESTART1R1R10 ==="
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

echo "=== Submitting Job M2STATE_FRACFIX_RESTART1R1R10 to PBS ==="
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART1R1R10.pbs)
echo "[SUBMISSION] Job submitted successfully: $JOB_ID"

if [ -f "$CANDIDATE_DIR/job_notifications.sh" ]; then
    source "$CANDIDATE_DIR/job_notifications.sh"
    notification_load_config
    notify_submitted "$JOB_ID" "M2STATE_FRACFIX_RESTART1R1R10" "entry_imfdfkmq" "1" "16gb" "24:00:00"
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
    print("Building M2STATE_FRACFIX_RESTART1R1R10 in %s" % OUT_DIR)

    # 1. Fortran UEL
    for_text = build_f42_mixed_uel_for()
    write_lf_file(OUT_DIR / "f42_mixed_uel.for", for_text)

    # 2. Input deck
    inp_text = generate_inp_deck()
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R10.inp", inp_text)

    # 3. PBS script
    pbs_text = generate_pbs_script()
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R10.pbs", pbs_text)

    # 4. Submission wrapper
    sh_text = generate_submit_wrapper()
    write_lf_file(OUT_DIR / "submit_m2state_fracfix_restart1r1r10.sh", sh_text)
    os.chmod(OUT_DIR / "submit_m2state_fracfix_restart1r1r10.sh", 0o755)

    # 5. Validator
    val_text = generate_validator_script()
    write_lf_file(OUT_DIR / "validate_package_manifest.py", val_text)
    os.chmod(OUT_DIR / "validate_package_manifest.py", 0o755)

    # 6. Notifications
    notif_text = SRC_NOTIF_SH.read_text(encoding="utf-8", errors="replace")
    write_lf_file(OUT_DIR / "job_notifications.sh", notif_text)

    # 7. Metadata records
    state_artifact = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R10",
        "task_id": "F93RECOVER-M2-INSTRUMENTED-RESTART1-R1R10-TECHNICAL-REPLACEMENT1",
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
        "notification_fix": "notification_load_config"
    }
    write_lf_file(OUT_DIR / "STATE_TRANSFER_ARTIFACT.json", json.dumps(state_artifact, indent=2))

    transfer_manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R10",
        "source_checkpoint": "1386469.mmaster02",
        "phase_field_transferred": True,
        "history_field_transferred": True,
        "target_physical_elements": 4894,
        "layered_total_elements": 14682,
        "uel_types": ["U1", "U2", "U3", "U4"]
    }
    write_lf_file(OUT_DIR / "TRANSFER_MANIFEST.json", json.dumps(transfer_manifest, indent=2))

    restart_contract = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R10",
        "force_continuity_tolerance": 0.02,
        "phase_continuity_tolerance": 0.02,
        "global_equilibrium_tolerance_kN": 1.0e-5,
        "cutback_tolerance": 0,
        "nan_tolerance": 0
    }
    write_lf_file(OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", json.dumps(restart_contract, indent=2))

    # 8. Package Manifest
    files_to_hash = [
        "M2STATE_FRACFIX_RESTART1R1R10.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART1R1R10.pbs",
        "submit_m2state_fracfix_restart1r1r10.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json"
    ]

    manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R10",
        "protocol_version": 1,
        "task_id": "F93RECOVER-M2-INSTRUMENTED-RESTART1-R1R10-TECHNICAL-REPLACEMENT1",
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
