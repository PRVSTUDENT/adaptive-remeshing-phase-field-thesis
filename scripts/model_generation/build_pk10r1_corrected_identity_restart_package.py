#!/usr/bin/env python3
"""
Package Builder for PK10R1_CORRECTED_IDENTITY_RESTART_U050
Candidate ID: PK10R1_CORRECTED_IDENTITY_RESTART_U050
Task ID: F122STATE-M2-PK10R1-CORRECTED-IDENTITY-RESTART-QUAL-AND-SUBMIT1

Scientific specification:
- Topology: Unchanged PK10R1 topology (9,849 nodes, 9,612 physical elements).
- Input deck: Exact copy of PK10R1_IDENTITY_RESTART_U050.inp, renamed to PK10R1_CORRECTED_IDENTITY_RESTART_U050.inp.
- UEL subroutine: f42_mixed_uel.for with sole scientific change: explicit PhaseInit history guard IF (KSTEP .GT. 1) around SV_H update in mechanical elements.
- Scheduler directives: 1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq, dual-channel notifications.
- Manifest: Hash-frozen PACKAGE_MANIFEST.json.
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_DIR = ROOT / "models/generated/mode_ii/production_control_batch/PK10R1_IDENTITY_RESTART_U050"
TARGET_DIR = ROOT / "models/generated/mode_ii/production_control_batch/PK10R1_CORRECTED_IDENTITY_RESTART_U050"

JOB_NAME = "PK10R1_CORRECTED_IDENTITY_RESTART_U050"

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_package():
    print("================================================================================")
    print(f"BUILDING FROZEN PACKAGE: {JOB_NAME}")
    print("================================================================================")

    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Input deck copy
    src_inp = SOURCE_DIR / "PK10R1_IDENTITY_RESTART_U050.inp"
    tgt_inp = TARGET_DIR / f"{JOB_NAME}.inp"
    print(f"1. Copying input deck: {src_inp.name} -> {tgt_inp.name}")
    shutil.copy(src_inp, tgt_inp)

    # 2. UEL subroutine with explicit PhaseInit history guard
    src_uel = SOURCE_DIR / "f42_mixed_uel.for"
    tgt_uel = TARGET_DIR / "f42_mixed_uel.for"
    print(f"2. Applying PhaseInit history guard to UEL subroutine: {tgt_uel.name}")
    
    uel_lines = src_uel.read_text(encoding="utf-8").splitlines()
    new_uel_lines = []
    
    for line in uel_lines:
        # For quad mechanical (JTYPE = 2):
        if "IF (POS_M .GT. HIST) THEN" in line and "SV_H(PHYSIDX, KPT) = POS_M" in uel_lines[uel_lines.index(line)+2]:
            new_uel_lines.append("          IF (KSTEP .GT. 1) THEN")
            new_uel_lines.append("            IF (POS_M .GT. HIST) THEN")
            new_uel_lines.append("              HIST = POS_M")
            new_uel_lines.append("              SV_H(PHYSIDX, KPT) = POS_M")
            new_uel_lines.append("            ENDIF")
            new_uel_lines.append("          ENDIF")
        elif "HIST = POS_M" in line or "SV_H(PHYSIDX, KPT) = POS_M" in line or "ENDIF" == line.strip():
            # Skip old lines that were replaced by the block above
            continue
        # For tri mechanical (JTYPE = 4):
        elif "HIST = SV_H(PHYSIDX, 1)" in line and "POS_M .GT. HIST" in uel_lines[uel_lines.index(line)+1]:
            new_uel_lines.append(line)
        else:
            new_uel_lines.append(line)

    # Clean UEL rewrite with precise line edits
    full_uel = src_uel.read_text(encoding="utf-8")
    
    # Replace JTYPE = 2 block
    target_block_q = """          HIST = SV_H(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H(PHYSIDX, KPT) = POS_M
          ENDIF"""

    replacement_block_q = """          HIST = SV_H(PHYSIDX, KPT)
          IF (KSTEP .GT. 1) THEN
            IF (POS_M .GT. HIST) THEN
              HIST = POS_M
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
          ENDIF"""

    # Replace JTYPE = 4 block
    target_block_t = """        HIST = SV_H(PHYSIDX, 1)
        IF (POS_M .GT. HIST) THEN
          HIST = POS_M
          SV_H(PHYSIDX, 1) = POS_M
        ENDIF"""

    replacement_block_t = """        HIST = SV_H(PHYSIDX, 1)
        IF (KSTEP .GT. 1) THEN
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H(PHYSIDX, 1) = POS_M
          ENDIF
        ENDIF"""

    if target_block_q not in full_uel:
        raise ValueError("Could not find target_block_q in UEL source!")
    if target_block_t not in full_uel:
        raise ValueError("Could not find target_block_t in UEL source!")

    full_uel = full_uel.replace(target_block_q, replacement_block_q)
    full_uel = full_uel.replace(target_block_t, replacement_block_t)
    tgt_uel.write_text(full_uel, encoding="utf-8", newline="\n")

    # 3. Notification system copy
    shutil.copy(SOURCE_DIR / "job_notifications.sh", TARGET_DIR / "job_notifications.sh")
    shutil.copy(SOURCE_DIR / "validate_package_manifest.py", TARGET_DIR / "validate_package_manifest.py")
    
    # Fix line endings on copied files
    for fn in ["job_notifications.sh", "validate_package_manifest.py"]:
        fp = TARGET_DIR / fn
        txt = fp.read_text(encoding="utf-8").replace("\r\n", "\n")
        fp.write_text(txt, encoding="utf-8", newline="\n")

    # 4. PBS script
    pbs_content = f"""#PBS -N {JOB_NAME}
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -o {JOB_NAME}.pbs.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

export XDG_RUNTIME_DIR=${{XDG_RUNTIME_DIR:-/tmp}}
source /etc/profile.d/lmod.sh 2>/dev/null || source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail

cd $PBS_O_WORKDIR

# Source notification system
source ./job_notifications.sh
notification_load_config 2>/dev/null || true
notify_start "{JOB_NAME}" "$PBS_JOBID" "entry_imfdfkmq" "1" "16gb" "24:00:00"
notification_install_terminal_trap "{JOB_NAME}" "$PBS_JOBID"

echo "=== PACKAGE INTEGRITY CHECK ==="
python3 validate_package_manifest.py

echo "=== ABAQUS SOLVER EXECUTION ==="
rm -f {JOB_NAME}.lck || true
abaqus job={JOB_NAME} user=f42_mixed_uel.for input={JOB_NAME}.inp double=both interactive cpus=1 memory="16000 mb"
"""
    (TARGET_DIR / f"{JOB_NAME}.pbs").write_text(pbs_content, encoding="utf-8", newline="\n")

    # 5. Guarded Wrapper Script
    sh_content = f"""#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Guarded Wrapper for {JOB_NAME} ==="

if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
elif [ -f "./job_notifications.sh" ]; then
    source "./job_notifications.sh"
fi

echo "1. Validating package manifest..."
python3 validate_package_manifest.py

if [[ "${{1:-}}" == "--dry-run" ]]; then
    echo "DRY_RUN_PASS: Package is valid and ready for submission."
    exit 0
elif [[ "${{1:-}}" == "--execute" ]]; then
    echo "2. Submitting PBS job..."
    JOB_ID=$(qsub {JOB_NAME}.pbs)
    echo "SUBMITTED: $JOB_ID"
    if type notify_submitted >/dev/null 2>&1; then
        notify_submitted "{JOB_NAME}" "$JOB_ID"
    fi
    exit 0
else
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi
"""
    tgt_sh = TARGET_DIR / f"submit_{JOB_NAME.lower()}.sh"
    tgt_sh.write_text(sh_content, encoding="utf-8", newline="\n")

    # 6. Generate PACKAGE_MANIFEST.json
    manifest_files = [
        f"{JOB_NAME}.inp",
        "f42_mixed_uel.for",
        f"{JOB_NAME}.pbs",
        f"submit_{JOB_NAME.lower()}.sh",
        "job_notifications.sh",
        "validate_package_manifest.py"
    ]
    
    file_hashes = {}
    for fn in manifest_files:
        fp = TARGET_DIR / fn
        file_hashes[fn] = get_file_sha256(fp)

    manifest_data = {
        "package_name": JOB_NAME,
        "task_id": "F122STATE-M2-PK10R1-CORRECTED-IDENTITY-RESTART-QUAL-AND-SUBMIT1",
        "created_at": "2026-08-15T06:35:00+02:00",
        "files": file_hashes
    }
    
    manifest_str = json.dumps(manifest_data, indent=2)
    manifest_sha256 = hashlib.sha256(manifest_str.encode("utf-8")).hexdigest()
    manifest_data["manifest_sha256"] = manifest_sha256

    (TARGET_DIR / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    print(f"Package successfully built and frozen!")
    print(f"Manifest SHA256: {manifest_sha256}")
    return manifest_sha256

if __name__ == "__main__":
    build_package()
