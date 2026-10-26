#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package114_companion_deck.py
==================================
Generates the authentic companion continuum input deck and qualification package
for Candidate C4 at exact Increment-79 loading state:
models/pandey_kumar_mode1/114_c4_inc79_companion_miseseri/

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 210)
Package: PACKAGE_114
State: Increment 79 Stationary Coupled State (u_RP = 0.001842500 mm, RF2 = 187.3915 N)
"""
import os
import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SRC_INP = REPO_ROOT / "models/pandey_kumar_mode1/95_c4_companion_miseseri/M1_C4_COMPANION_FRAME7.inp"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/114_c4_inc79_companion_miseseri"
OUT_INP = OUT_DIR / "M1_C4_INC79_COMPANION.inp"

INC79_U2_MM = 0.0018425000000000000
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_inc79_companion_miseseri"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SRC_INP, "r", encoding="utf-8") as f:
        src_text = f.read()

    # Replace Heading
    old_heading = """*Heading
** Mode-I C4 Companion Continuum Model for Authentic MISESERI Error Recovery
** State: Package 94 Step 4 Frame 7 Softened State (U2 = 0.002052000 mm)
** Protocol Version: 2 (Task F1597)"""

    new_heading = """*Heading
** Mode-I C4 Companion Continuum Model for Authentic MISESERI Error Recovery
** State: Increment 79 Pre-Peak Coupled State (U2 = %.9f mm, RF2 = 187.3915 N)
** Protocol Version: 2 (Task F1597, Package 114)""" % INC79_U2_MM

    if old_heading in src_text:
        mod_text = src_text.replace(old_heading, new_heading)
    else:
        # Fallback line-by-line replacement for heading
        lines = src_text.splitlines()
        for idx in range(min(10, len(lines))):
            if "State: Package 94" in lines[idx]:
                lines[idx] = "** State: Increment 79 Pre-Peak Coupled State (U2 = %.9f mm, RF2 = 187.3915 N)" % INC79_U2_MM
            if "Protocol Version: 2 (Task F1597)" in lines[idx]:
                lines[idx] = "** Protocol Version: 2 (Task F1597, Package 114)"
        mod_text = "\n".join(lines)

    # Replace boundary displacement at N_RP (node 999999)
    # Target: 999999, 2, 2, 0.002052000 -> 999999, 2, 2, 0.001842500
    old_bc = "999999, 2, 2, 0.002052000"
    new_bc = "999999, 2, 2, %.9f" % INC79_U2_MM
    if old_bc not in mod_text:
        raise RuntimeError("Old boundary condition card '%s' not found in source inp!" % old_bc)

    mod_text = mod_text.replace(old_bc, new_bc)

    with open(OUT_INP, "w", encoding="utf-8") as f:
        f.write(mod_text)

    inp_hash = sha256_file(OUT_INP)
    print("Wrote Package 114 companion input deck: %s (SHA256: %s)" % (OUT_INP, inp_hash))

    # Copy frozen UEL and job_notifications.sh
    src_uel = REPO_ROOT / "models/pandey_kumar_mode1/95_c4_companion_miseseri/f42_mixed_uel.for"
    dst_uel = OUT_DIR / "f42_mixed_uel.for"
    dst_uel.write_bytes(src_uel.read_bytes())
    frozen_uel_hash = sha256_file(dst_uel)

    src_notif = REPO_ROOT / "models/pandey_kumar_mode1/95_c4_companion_miseseri/job_notifications.sh"
    dst_notif = OUT_DIR / "job_notifications.sh"
    dst_notif.write_bytes(src_notif.read_bytes())
    notif_hash = sha256_file(dst_notif)

    # Build PBS script (pure LF)
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C4_INC79_COMP
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=01:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o {REMOTE_RUN_DIR}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="{REMOTE_RUN_DIR}"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C4_INC79_COMPANION"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

echo "=== C4 INC79 COMPANION CONTINUUM EXECUTION START ==="
echo "Host: $(hostname)"
echo "Date: $(date -Is)"
echo "PWD:  $(pwd)"

ABAQUS_CMD="abaqus job=M1_C4_INC79_COMPANION input=M1_C4_INC79_COMPANION.inp cpus=1 interactive"
echo "Running: ${{ABAQUS_CMD}}"
${{ABAQUS_CMD}}
EXIT_CODE=$?

echo "Abaqus completed with exit code: ${{EXIT_CODE}}"
if [ ${{EXIT_CODE}} -eq 0 ]; then
    echo "=== C4 INC79 COMPANION CONTINUUM SUCCESS ==="
else
    echo "=== C4 INC79 COMPANION CONTINUUM FAILED ==="
    exit ${{EXIT_CODE}}
fi
"""
    pbs_path = OUT_DIR / "submit_M1_C4_INC79_COMPANION.pbs"
    pbs_path.write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    pbs_hash = sha256_file(pbs_path)

    # Datacheck script (pure LF)
    datacheck_content = f"""#!/bin/bash
set -euo pipefail
RUN_DIR="{REMOTE_RUN_DIR}"
cd "${{RUN_DIR}}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load abaqus/2023

JOB_NAME="M1_C4_INC79_COMPANION_DC"
INP_NAME="M1_C4_INC79_COMPANION.inp"

rm -f ${{JOB_NAME}}.log ${{JOB_NAME}}.dat ${{JOB_NAME}}.msg ${{JOB_NAME}}.sta
echo "Starting Datacheck ${{JOB_NAME}} at $(date)"
abaqus job="${{JOB_NAME}}" input="${{INP_NAME}}" datacheck interactive
EXIT_CODE=$?
echo "Datacheck completed with exit code ${{EXIT_CODE}} at $(date)"
exit ${{EXIT_CODE}}
"""
    datacheck_path = OUT_DIR / "run_c4_inc79_companion_datacheck.sh"
    datacheck_path.write_bytes(datacheck_content.replace("\r\n", "\n").encode("utf-8"))
    datacheck_hash = sha256_file(datacheck_path)

    # PACKAGE_MANIFEST.json
    manifest = {
        "package_id": "PACKAGE_114",
        "description": "Mode-I Companion Continuum Linear Elastic Analysis on Candidate C4 for Authentic MISESERI Error Recovery at Increment 79 (u_RP = 0.001842500 mm)",
        "schema_version": 1,
        "model": "pandey_kumar_mode1",
        "files": {
            "M1_C4_INC79_COMPANION.inp": inp_hash,
            "f42_mixed_uel.for": frozen_uel_hash,
            "job_notifications.sh": notif_hash,
            "submit_M1_C4_INC79_COMPANION.pbs": pbs_hash,
            "run_c4_inc79_companion_datacheck.sh": datacheck_hash
        },
        "mesh": {
            "name": "Candidate C4",
            "quad_count": 4422,
            "node_count": 4588,
            "element_type": "CPE4",
            "process_zone_h_fine_mm": 0.000606
        },
        "loading": {
            "step": "STATIC_ELASTIC",
            "prescribed_u2_mm": INC79_U2_MM,
            "source_state": "Package 113 Stage C1-2 Increment 79 (u_RP = 0.001842500 mm, RF2 = 187.3915 N)"
        },
        "outputs_requested": [
            "S", "MISESERI", "MISESAVG", "EVOL"
        ]
    }
    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    manifest_hash = sha256_file(manifest_path)

    # Authorization JSON
    qsub_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_M1_C4_INC79_COMPANION.pbs"'
    cmd_hash = hashlib.sha256(qsub_cmd.encode("utf-8")).hexdigest().lower()

    auth = {
        "batch_name": "MODE1_PACKAGE_114_C4_INC79_COMPANION_MISESERI",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "files": {
            "M1_C4_INC79_COMPANION.inp": inp_hash.lower(),
            "f42_mixed_uel.for": frozen_uel_hash.lower(),
            "job_notifications.sh": notif_hash.lower(),
            "submit_M1_C4_INC79_COMPANION.pbs": pbs_hash.lower(),
            "PACKAGE_MANIFEST.json": manifest_hash.lower()
        },
        "jobs": [
            {
                "id": "M1_C4_INC79_COMPANION",
                "pbs": "submit_M1_C4_INC79_COMPANION.pbs",
                "command": qsub_cmd,
                "command_sha256": cmd_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 114: Companion continuum linear elastic solve on C4 mesh at Increment 79 state for authentic MISESERI error recovery",
                "cpus": 1,
                "memory_gb": 8,
                "walltime_hours": 1,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C4_INC79_COMPANION.inp",
                "datacheck": "M1_C4_INC79_COMPANION_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C4_INC79_COMPANION": "Exit code 0; authentic field outputs MISESERI, MISESAVG, S, EVOL captured in ODB for error-driven adaptation."
        }
    }
    auth_path = OUT_DIR / "M1_C4_INC79_COMPANION_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth, f, indent=2)

    print("Package 114 C4 Increment-79 companion continuum generation complete.")
    print("Files created in: %s" % OUT_DIR)

if __name__ == "__main__":
    main()
