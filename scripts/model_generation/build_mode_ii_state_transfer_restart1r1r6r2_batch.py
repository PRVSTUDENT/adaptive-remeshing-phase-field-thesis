#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart Candidate: M2STATE_FRACFIX_RESTART1R1R6R2.
Task ID: F57STATE-M2-FRACFIX-RESTART1R1R6R2-PREDEF-NULL-REPAIR1

Classification: RUNTIME_SAFETY_BUGFIX_PREDEF_NPREDF0
Canonical Manifest Key: "files"
Scientific formulation change count: 0 (100% identical mesh, state transfer, material parameters, UEL equations, loading).
All execution code dependencies packaged locally inside candidate directory.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_R1R6R1_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R1"
SRC_NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def write_lf_file(path: Path, text: str):
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(clean_text.encode("utf-8"))

def parse_physical_mesh(deck_path: Path):
    nodes: Dict[int, Tuple[float, float]] = {}
    quads: Dict[int, List[int]] = {}
    tris: Dict[int, List[int]] = {}
    bottom_nodes: List[int] = []
    top_nodes: List[int] = []

    lines = deck_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_part = False
    in_nodes = False
    in_cpe4 = False
    in_cpe3 = False
    in_bot_nset = False
    in_top_nset = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        s_upper = s.upper()

        if s_upper.startswith("*PART"):
            in_part = "PLATEPART" in s_upper
            continue
        if s_upper.startswith("*END PART"):
            in_part = False
            continue

        if in_part:
            if s_upper.startswith("*NODE"):
                in_nodes = True
                in_cpe4 = in_cpe3 = in_bot_nset = in_top_nset = False
                continue
            elif s_upper.startswith("*ELEMENT") and "TYPE=CPE4" in s_upper:
                in_cpe4 = True
                in_nodes = in_cpe3 = in_bot_nset = in_top_nset = False
                continue
            elif s_upper.startswith("*ELEMENT") and "TYPE=CPE3" in s_upper:
                in_cpe3 = True
                in_nodes = in_cpe4 = in_bot_nset = in_top_nset = False
                continue
            elif s_upper.startswith("*NSET") and "NSET=N_BOTTOM" in s_upper:
                in_bot_nset = True
                in_nodes = in_cpe4 = in_cpe3 = in_top_nset = False
                continue
            elif s_upper.startswith("*NSET") and "NSET=N_TOP" in s_upper:
                in_top_nset = True
                in_nodes = in_cpe4 = in_cpe3 = in_bot_nset = False
                continue
            elif s_upper.startswith("*"):
                in_nodes = in_cpe4 = in_cpe3 = in_bot_nset = in_top_nset = False
                continue

            if in_nodes:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif in_cpe4:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 5 and parts[0].isdigit():
                    quads[int(parts[0])] = [int(p) for p in parts[1:5]]
            elif in_cpe3:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 4 and parts[0].isdigit():
                    tris[int(parts[0])] = [int(p) for p in parts[1:4]]
            elif in_bot_nset:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                for p in parts:
                    if p.isdigit():
                        bottom_nodes.append(int(p))
            elif in_top_nset:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                for p in parts:
                    if p.isdigit():
                        top_nodes.append(int(p))

    return nodes, quads, tris, bottom_nodes, top_nodes

def build_standalone_validator() -> str:
    return """#!/usr/bin/env python3
\"\"\"
Standalone Package Manifest Validator for Production Candidate M2STATE_FRACFIX_RESTART1R1R6R2.
Eliminates all inline-Python shell-quoting vulnerabilities.
\"\"\"

import sys
import json
import hashlib
import re
from pathlib import Path

REQUIRED_FILES = [
    "M2STATE_FRACFIX_RESTART1R1R6R2.inp",
    "f42_mixed_uel.for",
    "STATE_TRANSFER_ARTIFACT.json",
    "TRANSFER_MANIFEST.json",
    "RESTART_ACCEPTANCE_CONTRACT.json",
    "verify_restart_trace.py",
    "extract_restart1r1r6_odb.py",
    "verify_restart1r1r6_science.py",
    "job_notifications.sh",
    "validate_package_manifest.py",
    "M2STATE_FRACFIX_RESTART1R1R6R2.pbs",
    "submit_m2state_fracfix_restart1r1r6r2.sh"
]

def validate_manifest(manifest_path_str: str = "PACKAGE_MANIFEST.json") -> bool:
    manifest_path = Path(manifest_path_str)
    if not manifest_path.exists():
        print(f"[PREFLIGHT] ERROR: Manifest not found: {manifest_path}")
        return False

    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[PREFLIGHT] ERROR: Failed to parse JSON manifest: {e}")
        return False

    if not isinstance(m, dict):
        print("[PREFLIGHT] ERROR: Manifest root is not a dictionary")
        return False

    if "files" not in m:
        print("[PREFLIGHT] ERROR: Canonical 'files' key missing from manifest")
        return False

    files_dict = m["files"]
    if not isinstance(files_dict, dict) or len(files_dict) == 0:
        print("[PREFLIGHT] ERROR: 'files' mapping is invalid or empty")
        return False

    for rf in REQUIRED_FILES:
        if rf not in files_dict:
            print(f"[PREFLIGHT] ERROR: Required execution file missing from manifest: {rf}")
            return False

    hex_re = re.compile(r"^[0-9a-fA-F]{64}$")
    for f_name, exp_hash in files_dict.items():
        if not isinstance(exp_hash, str) or not hex_re.match(exp_hash):
            print(f"[PREFLIGHT] ERROR: Invalid SHA256 format for {f_name}: {exp_hash}")
            return False
        f_path = manifest_path.parent / f_name if manifest_path.is_file() else Path(f_name)
        if not f_path.exists():
            print(f"[PREFLIGHT] ERROR: Required candidate file missing on disk: {f_name}")
            return False
        actual_hash = hashlib.sha256(f_path.read_bytes()).hexdigest()
        if actual_hash.lower() != exp_hash.lower():
            print(f"[PREFLIGHT] ERROR: Hash mismatch for {f_name}: expected {exp_hash}, got {actual_hash}")
            return False

    print("[PREFLIGHT] package_manifest_verification = PASS")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "PACKAGE_MANIFEST.json"
    if not validate_manifest(target):
        sys.exit(1)
    sys.exit(0)
"""

def build_r1r6r2_pbs_script() -> str:
    return """#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R6R2
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART1R1R6R2.pbs.log

cd $PBS_O_WORKDIR

# 1. Establish timing variables
JOB_START_EPOCH=$(date +%s)
echo "[PBS_PREFLIGHT] Starting M2STATE_FRACFIX_RESTART1R1R6R2 Production Restart Job..."
date

# 2. Source package-local notification helper and install terminal trap BEFORE manifest preflight
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

# 3. Standalone manifest preflight (zero inline Python, verifies all 12 package files)
python3 validate_package_manifest.py PACKAGE_MANIFEST.json
PREFLIGHT_RC=$?

if [ $PREFLIGHT_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Package manifest verification failed with exit code $PREFLIGHT_RC"
  exit $PREFLIGHT_RC
fi

# 4. Load Abaqus environment
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_PREFLIGHT] Abaqus environment loaded."
abaqus information=release

# 5. Run solver
abaqus job=M2STATE_FRACFIX_RESTART1R1R6R2 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R6R2.inp interactive

ABAQUS_RC=$?
echo "[PBS_PREFLIGHT] Abaqus execution finished with exit code $ABAQUS_RC"

if [ $ABAQUS_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Abaqus execution failed with exit code $ABAQUS_RC"
  exit $ABAQUS_RC
fi

echo "[PBS_PREFLIGHT] Abaqus continuation step completed successfully."

# 6. Postprocessing / trace checks
cat M2STATE_FRACFIX_RESTART1R1R6R2.dat M2STATE_FRACFIX_RESTART1R1R6R2.msg M2STATE_FRACFIX_RESTART1R1R6R2.log > M2STATE_FRACFIX_RESTART1R1R6R2.trace 2>/dev/null

python3 verify_restart_trace.py M2STATE_FRACFIX_RESTART1R1R6R2.trace
CHECKER_RC=$?

if [ $CHECKER_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Production restart trace checker failed with exit code $CHECKER_RC"
  exit $CHECKER_RC
fi

echo "[PBS_PREFLIGHT] ALL PRODUCTION RESTART CONTRACTS QUALIFIED SUCCESSFULLY."
"""

def build_r1r6r2_guarded_wrapper() -> str:
    return """#!/usr/bin/env bash
# Guarded Submission Wrapper for Production Candidate M2STATE_FRACFIX_RESTART1R1R6R2
# Candidate Revision: M2STATE_FRACFIX_RESTART1R1R6R2
# Author: Gemini Antigravity
# Protocol Version: 1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_MANIFEST="${SCRIPT_DIR}/PACKAGE_MANIFEST.json"
PBS_SCRIPT="${SCRIPT_DIR}/M2STATE_FRACFIX_RESTART1R1R6R2.pbs"
CANDIDATE_NAME="M2STATE_FRACFIX_RESTART1R1R6R2"

DRY_RUN=false
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    fi
done

echo "======================================================================"
echo "[PREFLIGHT] Validating package integrity for ${CANDIDATE_NAME}..."
echo "======================================================================"

if [[ ! -f "${PACKAGE_MANIFEST}" ]]; then
    echo "[PREFLIGHT] ERROR: Manifest file missing: ${PACKAGE_MANIFEST}" >&2
    exit 1
fi

if [[ ! -f "${PBS_SCRIPT}" ]]; then
    echo "[PREFLIGHT] ERROR: PBS script missing: ${PBS_SCRIPT}" >&2
    exit 1
fi

NOTIF_HELPER="${SCRIPT_DIR}/job_notifications.sh"
if [[ ! -f "${NOTIF_HELPER}" ]]; then
    NOTIF_HELPER="${HOME}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
fi

if [[ -f "${NOTIF_HELPER}" ]]; then
    source "${NOTIF_HELPER}"
fi

echo "[PREFLIGHT] Checking package execution files..."
for f in "M2STATE_FRACFIX_RESTART1R1R6R2.inp" "f42_mixed_uel.for" "STATE_TRANSFER_ARTIFACT.json" "TRANSFER_MANIFEST.json" "RESTART_ACCEPTANCE_CONTRACT.json" "job_notifications.sh" "validate_package_manifest.py" "extract_restart1r1r6_odb.py" "verify_restart1r1r6_science.py"; do
    if [[ ! -f "${SCRIPT_DIR}/${f}" ]]; then
        echo "[PREFLIGHT] ERROR: Required candidate file missing: ${f}" >&2
        exit 1
    fi
done

# Run standalone validator
python3 "${SCRIPT_DIR}/validate_package_manifest.py" "${PACKAGE_MANIFEST}"
echo "[PREFLIGHT] Package files present and verified."

if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[PREFLIGHT] Dry-run verification PASS."
    echo "[PREFLIGHT] Intended command: qsub ${PBS_SCRIPT}"
    echo "[PREFLIGHT] No qsub invoked during dry run."
    exit 0
fi

echo "======================================================================"
echo "[SUBMIT] Submitting ${CANDIDATE_NAME} to PBS scheduler..."
echo "======================================================================"

QSUB_BIN="qsub"
if [[ -n "${MOCK_QSUB_BIN:-}" ]]; then
    QSUB_BIN="${MOCK_QSUB_BIN}"
fi

JOB_OUTPUT=$("${QSUB_BIN}" "${PBS_SCRIPT}")
JOB_ID=$(echo "${JOB_OUTPUT}" | tail -n 1)

echo "[SUBMIT] SUCCESS: Job submitted as ${JOB_ID}"

if declare -f notify_submitted >/dev/null 2>&1; then
    notify_submitted "${JOB_ID}" "${CANDIDATE_NAME}" "Submitted to PBS queue entry_imfdfkmq (1 CPU, 8GB, 24:00:00)" || echo "[SUBMIT] WARNING: Submission notification delivery failed" >&2
elif declare -f notify_event >/dev/null 2>&1; then
    notify_event "SUBMITTED" "${JOB_ID}" "${CANDIDATE_NAME}" "Submitted to PBS queue entry_imfdfkmq" || echo "[SUBMIT] WARNING: Submission notification delivery failed" >&2
fi

exit 0
"""

def repair_f42_uel(src_uel_path: Path) -> str:
    """
    Remove errant PREDEF(1,1,1)=0.D0 statement in JTYPE=4 branch while preserving all equations and comments.
    """
    src_lines = src_uel_path.read_text(encoding="utf-8").splitlines()
    repaired_lines = []
    
    deleted_count = 0
    for i, line in enumerate(src_lines):
        # Update revision comment
        if "Candidate Revision: M2STATE_FRACFIX_RESTART1R1R6" in line:
            repaired_lines.append("C Candidate Revision: M2STATE_FRACFIX_RESTART1R1R6R2 (Runtime Safety Bugfix PREDEF NPREDF=0)")
            continue
            
        # Target errant statement on line 352
        if "PREDEF(1,1,1)=0.D0" in line:
            # We delete this line completely
            deleted_count += 1
            continue
            
        repaired_lines.append(line)
        
    if deleted_count != 1:
        raise RuntimeError(f"Expected to delete exactly 1 PREDEF line, deleted {deleted_count}")
        
    return "\n".join(repaired_lines) + "\n"

def main():
    print("======================================================================")
    print("BUILDING PRODUCTION CANDIDATE: M2STATE_FRACFIX_RESTART1R1R6R2")
    print("======================================================================")
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Input deck
    inp_src = SRC_R1R6R1_DIR / "M2STATE_FRACFIX_RESTART1R1R6R1.inp"
    inp_text = inp_src.read_text(encoding="utf-8")
    inp_r1r6r2 = inp_text.replace("M2STATE_FRACFIX_RESTART1R1R6R1", "M2STATE_FRACFIX_RESTART1R1R6R2")
    inp_dst = OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R6R2.inp"
    write_lf_file(inp_dst, inp_r1r6r2)
    print(f"Created input deck: {inp_dst.name} ({len(inp_r1r6r2)} bytes)")
    
    # 2. User subroutine (with PREDEF write deleted)
    uel_src = SRC_R1R6R1_DIR / "f42_mixed_uel.for"
    uel_repaired = repair_f42_uel(uel_src)
    uel_dst = OUT_DIR / "f42_mixed_uel.for"
    write_lf_file(uel_dst, uel_repaired)
    print(f"Created repaired UEL Fortran: {uel_dst.name} ({len(uel_repaired)} bytes)")
    
    # 3. Artifacts and contracts
    for f in ["STATE_TRANSFER_ARTIFACT.json", "TRANSFER_MANIFEST.json", "RESTART_ACCEPTANCE_CONTRACT.json"]:
        src = SRC_R1R6R1_DIR / f
        dst = OUT_DIR / f
        data = json.loads(src.read_text(encoding="utf-8"))
        if "candidate" in data:
            data["candidate"] = "M2STATE_FRACFIX_RESTART1R1R6R2"
        write_lf_file(dst, json.dumps(data, indent=2) + "\n")
        print(f"Copied & updated: {f}")
        
    # 4. Helpers
    checker_src = SRC_R1R6R1_DIR / "verify_restart_trace.py"
    checker_dst = OUT_DIR / "verify_restart_trace.py"
    write_lf_file(checker_dst, checker_src.read_text(encoding="utf-8"))
    print(f"Copied trace checker: {checker_dst.name}")
    
    for f in ["extract_restart1r1r6_odb.py", "verify_restart1r1r6_science.py"]:
        src = SRC_R1R6R1_DIR / f
        dst = OUT_DIR / f
        write_lf_file(dst, src.read_text(encoding="utf-8"))
        print(f"Copied postprocessing helper: {f}")
        
    # 5. Package-local notification helper
    notif_dst = OUT_DIR / "job_notifications.sh"
    write_lf_file(notif_dst, SRC_NOTIF_SH.read_text(encoding="utf-8"))
    print(f"Copied package-local notification helper: {notif_dst.name}")
    
    # 6. Standalone validator
    val_dst = OUT_DIR / "validate_package_manifest.py"
    write_lf_file(val_dst, build_standalone_validator())
    print(f"Created standalone validator: {val_dst.name}")
    
    # 7. PBS script
    pbs_dst = OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R6R2.pbs"
    write_lf_file(pbs_dst, build_r1r6r2_pbs_script())
    print(f"Created PBS script: {pbs_dst.name}")
    
    # 8. Guarded wrapper
    wrapper_dst = OUT_DIR / "submit_m2state_fracfix_restart1r1r6r2.sh"
    write_lf_file(wrapper_dst, build_r1r6r2_guarded_wrapper())
    print(f"Created guarded wrapper: {wrapper_dst.name}")
    
    # 9. Package Manifest
    files_to_hash = [
        "M2STATE_FRACFIX_RESTART1R1R6R2.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "verify_restart_trace.py",
        "extract_restart1r1r6_odb.py",
        "verify_restart1r1r6_science.py",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R6R2.pbs",
        "submit_m2state_fracfix_restart1r1r6r2.sh"
    ]
    
    manifest_hashes = {}
    for f in files_to_hash:
        p = OUT_DIR / f
        manifest_hashes[f] = sha256_file(p)
        
    manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R6R2",
        "predecessor": "M2STATE_FRACFIX_RESTART1R1R6R1",
        "classification": "RUNTIME_SAFETY_BUGFIX_PREDEF_NPREDF0",
        "scientific_formulation_change_count": 0,
        "files": manifest_hashes
    }
    
    manifest_dst = OUT_DIR / "PACKAGE_MANIFEST.json"
    write_lf_file(manifest_dst, json.dumps(manifest, indent=2) + "\n")
    print(f"Created manifest: {manifest_dst.name}")
    
    print("======================================================================")
    print("M2STATE_FRACFIX_RESTART1R1R6R2 BUILDING COMPLETE")
    print("======================================================================")

if __name__ == "__main__":
    main()
