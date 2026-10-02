#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rebuild and Validate M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL
Directly from 1391300.mmaster02 (R1)
"""

import os
import sys
import shutil
import hashlib
import json
import difflib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def clean_lf(filepath):
    with open(filepath, "rb") as f:
        content = f.read()
    content_lf = content.replace(b"\r\n", b"\n")
    with open(filepath, "wb") as f:
        f.write(content_lf)

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    r1_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL")
    r2_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL")

    if not os.path.exists(r2_dir):
        os.makedirs(r2_dir)

    r1_inp_path = os.path.join(r1_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.inp")
    r2_inp_path = os.path.join(r2_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL.inp")

    with open(r1_inp_path, "r") as f:
        r1_lines = f.readlines()

    r2_lines = []
    in_step3 = False
    in_step4 = False
    s3_static_modified = False
    s3_controls_modified = False

    for line in r1_lines:
        l_strip = line.strip()
        if "*STEP, NAME=PHASE_RELEASE" in line:
            in_step3 = True
            in_step4 = False
        elif "*STEP, NAME=CONTINUATION" in line:
            in_step3 = False
            in_step4 = True
        elif "*END STEP" in line:
            in_step3 = False
            in_step4 = False

        if in_step3 and l_strip == "0.001, 1.0, 1.0e-11, 1.0":
            r2_lines.append("0.001, 1.0, 5.0e-12, 1.0\n")
            s3_static_modified = True
        elif in_step3 and l_strip == "4, 8, 9, 16, 10, 4, 50, 12":
            r2_lines.append("4, 8, 9, 16, 10, 4, 50, 13\n")
            s3_controls_modified = True
        else:
            r2_lines.append(line)

    assert s3_static_modified, "FATAL: Step 3 STATIC was not modified!"
    assert s3_controls_modified, "FATAL: Step 3 CONTROLS was not modified!"

    with open(r2_inp_path, "w") as f:
        f.writelines(r2_lines)
    clean_lf(r2_inp_path)

    # Copy support files verbatim
    for fname in ["STAGE_D_COMMITTED_STATE.bin", "f44_mixed_uel_restart_stateinit.for", "MODE_STAGED.flag",
                  "STAGE_E_PRIMARY_STATE_BOUNDARY.inp", "STAGE_E_U3_ONLY_BOUNDARY.inp"]:
        src_f = os.path.join(r1_dir, fname)
        dst_f = os.path.join(r2_dir, fname)
        shutil.copy2(src_f, dst_f)
        if fname != "STAGE_D_COMMITTED_STATE.bin":
            clean_lf(dst_f)

    pbs_content = """#!/bin/bash
#PBS -N M2E_REF_R2_VAL
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR || exit 1

# Clean old lock files
rm -f *.lck

# Correct compute-node module sequence
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

export PYTHONUNBUFFERED=1
JOBNAME=M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL
USER_SUBROUTINE=f44_mixed_uel_restart_stateinit.for

echo "[PBS] Starting job $PBS_JOBID on host $(hostname) at $(date)"
abaqus job=$JOBNAME input=$JOBNAME.inp user=$USER_SUBROUTINE cpus=1 interactive
EXIT_STATUS=$?
echo "[PBS] Solver execution exited with status $EXIT_STATUS at $(date)"
exit $EXIT_STATUS
"""
    dst_pbs = os.path.join(r2_dir, "submit_job.pbs")
    with open(dst_pbs, "w") as f:
        f.write(pbs_content)
    clean_lf(dst_pbs)

    # Clean LF on R1 to ensure identical line ending comparison
    clean_lf(r1_inp_path)

    with open(r1_inp_path, "r") as f1, open(r2_inp_path, "r") as f2:
        r1_norm = f1.readlines()
        r2_norm = f2.readlines()

    udiff = list(difflib.unified_diff(r1_norm, r2_norm, fromfile="1391300_R1", tofile="M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL", lineterm="\n"))

    print("================================================================================")
    print("EXACT NORMALIZED / BYTE-LEVEL DIFF (R1 vs Reconciled R2):")
    print("================================================================================")
    for line in udiff:
        print(line.rstrip())
    print("================================================================================")

    diff_added = [l for l in udiff if l.startswith("+") and not l.startswith("+++")]
    diff_removed = [l for l in udiff if l.startswith("-") and not l.startswith("---")]
    print("Diff lines removed count: %d" % len(diff_removed))
    print("Diff lines added count  : %d" % len(diff_added))
    assert len(diff_removed) == 2, "FATAL: Expected exactly 2 removed lines!"
    assert len(diff_added) == 2, "FATAL: Expected exactly 2 added lines!"
    assert "-0.001, 1.0, 1.0e-11, 1.0" in diff_removed[0], "Diff mismatch on line 1"
    assert "+0.001, 1.0, 5.0e-12, 1.0" in diff_added[0], "Diff mismatch on line 1"
    assert "-4, 8, 9, 16, 10, 4, 50, 12" in diff_removed[1], "Diff mismatch on line 2"
    assert "+4, 8, 9, 16, 10, 4, 50, 13" in diff_added[1], "Diff mismatch on line 2"
    print("DIFF PROOF VERIFIED: EXACTLY AND ONLY THE TWO QUALIFIED STEP-3 CONTROLS DIFFER!")

    # Verify Step 4 unchanged
    s4_static_lines = [l for l in r2_lines if "0.001, 1.0, 1.0e-11, 0.02" in l]
    assert len(s4_static_lines) == 1, "FATAL: Step 4 STATIC modified or missing!"
    print("Step 4 CONTINUATION STATIC: 0.001, 1.0, 1.0e-11, 0.02 (UNMODIFIED)")
    print("Step 4 CONTINUATION CONTROLS: 4, 8, 9, 16, 10, 4, 50, 12 (UNMODIFIED)")

    # Mesh and Model Verification
    in_phase = False
    in_mech = False
    in_nodes = False
    phase_elems = 0
    mech_elems = 0
    phys_nodes = 0
    for l in r2_lines:
        l_s = l.strip()
        if l_s.startswith("*ELEMENT, TYPE=U1"):
            in_phase = True
            in_mech = False
            in_nodes = False
        elif l_s.startswith("*ELEMENT, TYPE=U2"):
            in_phase = False
            in_mech = True
            in_nodes = False
        elif l_s == "*NODE" or l_s.startswith("*NODE,"):
            in_phase = False
            in_mech = False
            in_nodes = True
        elif l_s.startswith("*"):
            in_phase = False
            in_mech = False
            in_nodes = False
        else:
            if in_phase and l_s:
                phase_elems += 1
            elif in_mech and l_s:
                mech_elems += 1
            elif in_nodes and l_s:
                nid = int(l_s.split(",")[0].strip())
                if nid != 99999:
                    phys_nodes += 1

    print("Mesh Topology: Phase UELs=%d, Mech UELs=%d, Total UELs=%d, Physical Nodes=%d" % (
        phase_elems, mech_elems, phase_elems + mech_elems, phys_nodes))
    assert phase_elems == 33600 and mech_elems == 33600, "FATAL: Element count mismatch!"
    assert phys_nodes == 34027, "FATAL: Physical node count mismatch!"

    # Hash verification
    inp_sha = sha256_file(r2_inp_path)
    bin_sha = sha256_file(os.path.join(r2_dir, "STAGE_D_COMMITTED_STATE.bin"))
    for_sha = sha256_file(os.path.join(r2_dir, "f44_mixed_uel_restart_stateinit.for"))
    pbs_sha = sha256_file(os.path.join(r2_dir, "submit_job.pbs"))
    pbc_sha = sha256_file(os.path.join(r2_dir, "STAGE_E_PRIMARY_STATE_BOUNDARY.inp"))
    u3bc_sha = sha256_file(os.path.join(r2_dir, "STAGE_E_U3_ONLY_BOUNDARY.inp"))
    flag_sha = sha256_file(os.path.join(r2_dir, "MODE_STAGED.flag"))

    print("\nHASHES:")
    print("  INP SHA256: %s" % inp_sha)
    print("  BIN SHA256: %s (size=%d bytes)" % (bin_sha, os.path.getsize(os.path.join(r2_dir, "STAGE_D_COMMITTED_STATE.bin"))))
    print("  FOR SHA256: %s" % for_sha)
    print("  PBS SHA256: %s" % pbs_sha)

    assert bin_sha == sha256_file(os.path.join(r1_dir, "STAGE_D_COMMITTED_STATE.bin"))
    assert for_sha == sha256_file(os.path.join(r1_dir, "f44_mixed_uel_restart_stateinit.for"))
    assert pbc_sha == sha256_file(os.path.join(r1_dir, "STAGE_E_PRIMARY_STATE_BOUNDARY.inp"))
    assert u3bc_sha == sha256_file(os.path.join(r1_dir, "STAGE_E_U3_ONLY_BOUNDARY.inp"))
    assert flag_sha == sha256_file(os.path.join(r1_dir, "MODE_STAGED.flag"))
    print("SUPPORT FILES INTEGRITY VERIFIED: ALL BIT-FOR-BIT IDENTICAL TO R1!")

    # Write Manifest
    manifest_data = {
        "package_name": "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL",
        "base_job": "1391300.mmaster02",
        "base_package": "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL",
        "provenance": {
            "source_donor_job": "1390447.mmaster02",
            "source_donor_frame": 17,
            "source_donor_u1_mm": 0.01051289,
            "donor_qualification_job": "1391319.mmaster02",
            "donor_qualification_status": "COMBINED_PATH_NEUTRAL_VALIDATED",
            "target_mesh": "Refined (33,600 quads, 34,027 nodes, h_tip=0.002 mm)",
            "history_operator": "HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP"
        },
        "mesh_verification": {
            "physical_quads": 33600,
            "physical_nodes_excl_rp": 34027,
            "total_uel_count": 67200,
            "mech_uels": 33600,
            "phase_uels": 33600,
            "h_min_mm": 0.002,
            "props": [0.00375, 0.0027, 210.0, 0.3, 1e-07, 33600.0, 1.0]
        },
        "step_controls": {
            "Step_1_STATE_INSTALL": {
                "STATIC": "1.0, 1.0, 1.0e-5, 1.0",
                "CONTROLS": "Default"
            },
            "Step_2_MECH_EQUILIBRATION": {
                "STATIC": "1.0, 1.0, 1.0e-5, 1.0",
                "CONTROLS": "Default"
            },
            "Step_3_PHASE_RELEASE": {
                "STATIC": "0.001, 1.0, 5.0e-12, 1.0",
                "CONTROLS": "4, 8, 9, 16, 10, 4, 50, 13"
            },
            "Step_4_CONTINUATION": {
                "STATIC": "0.001, 1.0, 1.0e-11, 0.02",
                "CONTROLS": "4, 8, 9, 16, 10, 4, 50, 12"
            }
        },
        "hashes": {
            "inp_sha256": inp_sha,
            "for_sha256": for_sha,
            "bin_sha256": bin_sha,
            "pbs_sha256": pbs_sha,
            "primary_bcs_sha256": pbc_sha,
            "u3_bcs_sha256": u3bc_sha,
            "flag_sha256": flag_sha
        },
        "one_difference_audit": {
            "mesh_changed": False,
            "state_binary_changed": False,
            "uel_subroutine_changed": False,
            "material_props_changed": False,
            "step_semantics_changed": False,
            "step1_state_install_changed": False,
            "step2_mech_equilibration_changed": False,
            "step3_phase_release_controls_modified": True,
            "step3_changes": {
                "before_r1": {
                    "static_card": "0.001, 1.0, 1.0e-11, 1.0",
                    "controls_card": "4, 8, 9, 16, 10, 4, 50, 12",
                    "I_A": 12,
                    "dt_min": "1.0e-11"
                },
                "after_r2": {
                    "static_card": "0.001, 1.0, 5.0e-12, 1.0",
                    "controls_card": "4, 8, 9, 16, 10, 4, 50, 13",
                    "I_A": 13,
                    "dt_min": "5.0e-12"
                }
            },
            "step4_continuation_controls_modified": False,
            "step4_controls": {
                "static_card": "0.001, 1.0, 1.0e-11, 0.02",
                "controls_card": "4, 8, 9, 16, 10, 4, 50, 12",
                "I_A": 12,
                "dt_min": "1.0e-11"
            }
        },
        "unified_diff": [l.rstrip() for l in udiff],
        "submission_authorized": False
    }

    manifest_path = os.path.join(base_dir, "refined_r2_manifest.json")
    with open(manifest_path, "w") as fp:
        json.dump(manifest_data, fp, indent=2)

    replacement_manifest_path = os.path.join(base_dir, "refined_r2_replacement_manifest.json")
    with open(replacement_manifest_path, "w") as fp:
        json.dump(manifest_data, fp, indent=2)

    print("Saved Manifests to:\n  %s\n  %s" % (manifest_path, replacement_manifest_path))

if __name__ == "__main__":
    main()
