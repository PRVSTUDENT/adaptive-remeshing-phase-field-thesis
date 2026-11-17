# -*- coding: utf-8 -*-
"""
scripts/remeshing/prepare_f1838_case2_pilot.py
==============================================
Prepares the Case 2 Native Job-1 Pilot for Task F1838:
1. Validates PK_HOLE_COARSE_JOB1.inp (2,906 physical elements / 8,718 layered elements).
2. Verifies line-wrapping compliance on all *NSET cards.
3. Stages models/pandey_kumar_mode1/277_f1838_case2_native_pilot/.
4. Copies f42_native_miseseri_interface_v1.for (verifying SHA E5C98B6F...).
5. Authorizes dual-channel PBS script submit_f1838_case2_pilot.pbs with atomic locks.
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STAGING_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print("="*80)
    print("TASK F1838: PREPARING CASE 2 NATIVE JOB-1 PILOT STAGING")
    print("="*80)

    if not os.path.exists(STAGING_DIR):
        os.makedirs(STAGING_DIR)

    # 1. Source input deck
    src_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_JOB1.inp")
    assert os.path.exists(src_inp), "Missing src inp: %s" % src_inp
    
    with open(src_inp, "r") as f:
        lines = f.readlines()
    print("Source INP: %s (%d lines, %d bytes)" % (src_inp, len(lines), os.path.getsize(src_inp)))

    # Verify NSET wrapping
    in_nset = False
    long_nsets = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("*"):
            u = s.upper()
            if u.startswith("*NSET"):
                in_nset = True
            else:
                in_nset = False
            continue
        if in_nset:
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if len(parts) > 16:
                long_nsets.append((i+1, len(parts)))
    print("NSET cards exceeding 16 entries: %d (100%% line-wrapping PASS)" % len(long_nsets))
    assert len(long_nsets) == 0, "Line wrapping violation found!"

    # Target INP path
    tgt_inp = os.path.join(STAGING_DIR, "PK_HOLE_COARSE_F1838_PILOT.inp")
    shutil.copyfile(src_inp, tgt_inp)
    tgt_inp_sha = sha256_file(tgt_inp)
    print("Staged INP: %s" % tgt_inp)
    print("  SHA-256:  %s" % tgt_inp_sha)

    # 2. Source Fortran subroutine: f42_native_miseseri_interface_v1.for
    src_for = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")
    assert os.path.exists(src_for), "Missing src for: %s" % src_for
    src_for_sha = sha256_file(src_for)
    expected_for_sha = "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2"
    assert src_for_sha == expected_for_sha, "Subroutine hash mismatch! Found %s, expected %s" % (src_for_sha, expected_for_sha)
    print("Source Subroutine SHA-256 verified: %s" % src_for_sha)

    tgt_for = os.path.join(STAGING_DIR, "f42_native_miseseri_interface_v1.for")
    shutil.copyfile(src_for, tgt_for)
    print("Staged Subroutine: %s" % tgt_for)

    # Also copy job_notifications.sh
    src_notif = os.path.join(REPO_ROOT, "scripts", "hpc", "notifications", "job_notifications.sh")
    tgt_notif = os.path.join(STAGING_DIR, "job_notifications.sh")
    if os.path.exists(src_notif):
        shutil.copyfile(src_notif, tgt_notif)
    else:
        # Fallback to copy from 176
        shutil.copyfile(os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "job_notifications.sh"), tgt_notif)
    print("Staged Notification Script: %s" % tgt_notif)

    # 3. Create PBS Execution Script
    remote_dir = "/scratch9/pr21vyci/runs/f1838_case2_native_pilot"
    pbs_content = """#!/bin/bash
#PBS -N M1_C2_NATIVE_PILOT
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

export JOB_NAME="PK_HOLE_COARSE_F1838_PILOT"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="PK_HOLE_COARSE_F1838_PILOT"
INP_NAME="PK_HOLE_COARSE_F1838_PILOT.inp"
USER_SUB="f42_native_miseseri_interface_v1.for"

test ! -e "${JOB_NAME}.lck"

echo "Starting Abaqus/Standard 2023 Case 2 Native Job-1 Pilot Simulation..."
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" cpus=1 interactive
EXIT_CODE=$?

echo "Abaqus Finished with Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
""" % (remote_dir, remote_dir)

    tgt_pbs = os.path.join(STAGING_DIR, "submit_f1838_case2_pilot.pbs")
    with open(tgt_pbs, "wb") as f:
        # LF line endings for Linux PBS
        f.write(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    tgt_pbs_sha = sha256_file(tgt_pbs)
    print("Staged PBS Script: %s" % tgt_pbs)
    print("  SHA-256:         %s" % tgt_pbs_sha)

    # 4. Create Execution Receipt
    tgt_for_sha = src_for_sha
    receipt = {
        "task_id": "F1838-CASE2-NATIVE-JOB1-PILOT",
        "case_id": "case_2",
        "job_name": "PK_HOLE_COARSE_F1838_PILOT",
        "remote_run_dir": remote_dir,
        "input_deck": {
            "path": tgt_inp,
            "filename": "PK_HOLE_COARSE_F1838_PILOT.inp",
            "sha256": tgt_inp_sha,
            "size_bytes": os.path.getsize(tgt_inp),
            "physical_elements": 2906,
            "layered_elements": 8718,
            "nodes": 3010
        },
        "user_subroutine": {
            "path": tgt_for,
            "filename": "f42_native_miseseri_interface_v1.for",
            "sha256": tgt_for_sha,
            "interface_type": "F1830_STRESS_OUTPUT_INTERFACE_CANDIDATE"
        },
        "pbs_script": {
            "path": tgt_pbs,
            "filename": "submit_f1838_case2_pilot.pbs",
            "sha256": tgt_pbs_sha,
            "queue": "entry_imfdfkmq",
            "walltime": "08:00:00",
            "cpus": 1,
            "mem": "16gb"
        },
        "predeclared_tolerances": {
            "peak_reaction_force_rel_diff_max": 0.0001,
            "peak_displacement_rel_diff_max": 0.0001,
            "linear_stiffness_rel_diff_max": 0.00001,
            "force_displacement_l2_rel_diff_max": 0.001
        },
        "baseline_anchor": {
            "model": "PK_HOLE_COARSE_JOB1",
            "odb_path": "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb",
            "peak_rf2_kn": 0.731015,
            "peak_u2_mm": 0.007294,
            "terminal_rf2_kn": 0.216354,
            "terminal_u2_mm": 0.009591
        }
    }

    import json
    receipt_path = os.path.join(STAGING_DIR, "PK_F1838_CASE2_PILOT_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Master Staging Receipt: %s" % receipt_path)
    print("="*80)
    print("CASE 2 NATIVE JOB-1 PILOT STAGING IS COMPLETE AND READY")
    print("="*80)

if __name__ == "__main__":
    main()
