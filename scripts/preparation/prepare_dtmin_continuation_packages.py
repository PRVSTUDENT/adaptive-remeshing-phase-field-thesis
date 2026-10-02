#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Preparation of Minimal dt_min Continuation Qualification Packages (Non-submitting):
1. Donor Package: M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL
   - Derived from: M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL (Job 1390552)
   - Only scientific difference: dt_min: 1.0e-9 -> 1.0e-11 in *STATIC
   - Controls preserved: I_A=12, I_0=4, I_R=8, I_P=9, I_C=16, I_L=10, I_G=4, I_S=50
2. Refined Package: M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL
   - Derived from: M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL (Job 1390834)
   - Only scientific difference: dt_min: 1.0e-9 -> 1.0e-11 in *STATIC
"""

import os
import sys
import shutil
import hashlib
import json

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def prepare_package(src_dir, src_name, dst_dir, dst_name, cand_dtmin_str="1.0e-11"):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    src_inp = os.path.join(src_dir, src_name + ".inp")
    dst_inp = os.path.join(dst_dir, dst_name + ".inp")
    
    with open(src_inp, "r") as f:
        lines = f.readlines()
        
    new_lines = []
    in_static = False
    static_modified = False
    
    for idx, line in enumerate(lines):
        if line.strip().upper().startswith("*STATIC"):
            in_static = True
            new_lines.append(line)
            continue
            
        if in_static and not static_modified:
            # Format is typically: 0.001, 1.0, 1.0e-9, 0.02
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                parts[2] = cand_dtmin_str
                new_line = ", ".join(parts) + "\n"
                new_lines.append(new_line)
                static_modified = True
                in_static = False
                continue
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(dst_inp, "wb") as f:
        for nl in new_lines:
            f.write(nl.encode('utf-8'))
            
    # Copy UEL subroutine
    src_for = os.path.join(src_dir, "f44_mixed_uel_restart_stateinit.for")
    dst_for = os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for")
    shutil.copyfile(src_for, dst_for)
    
    # Create strict Unix LF PBS script
    dst_pbs = os.path.join(dst_dir, "submit_job.pbs")
    pbs_content = """#!/bin/bash
#PBS -N %(job_name)s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o pbs.out
#PBS -e pbs.err

cd "$PBS_O_WORKDIR" || exit 1

module purge
module load intel/2024.2.0
module load abaqus/2024

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode start --job-name "%(job_name)s"

abaqus job=%(job_name)s user=f44_mixed_uel_restart_stateinit.for input=%(job_name)s.inp interactive memory="14gb"
ABAQUS_RC=$?

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode end --job-name "%(job_name)s" --exit-code "$ABAQUS_RC"

exit "$ABAQUS_RC"
""" % {"job_name": dst_name[:15]}
    
    with open(dst_pbs, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode('utf-8'))
        
    return {
        "src_inp_sha256": get_file_sha256(src_inp),
        "dst_inp_sha256": get_file_sha256(dst_inp),
        "dst_for_sha256": get_file_sha256(dst_for),
        "dst_pbs_sha256": get_file_sha256(dst_pbs)
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Donor Package
    donor_src_dir = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL")
    donor_dst_dir = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL")
    donor_res = prepare_package(
        donor_src_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL",
        donor_dst_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
        "1.0e-11"
    )
    
    # 2. Refined Package
    ref_src_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL")
    ref_dst_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    ref_res = prepare_package(
        ref_src_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL",
        ref_dst_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL",
        "1.0e-11"
    )
    
    manifest = {
        "candidate_dt_min": "1.0e-11",
        "rationale": "Derived from geometric progression with D_A=0.25 from Attempt 9 (2.864e-9 s), allowing full 12 attempts down to 4.475e-11 s without floor clamping.",
        "donor_package": {
            "name": "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
            "dir": donor_dst_dir,
            "provenance": donor_res
        },
        "refined_package": {
            "name": "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL",
            "dir": ref_dst_dir,
            "provenance": ref_res
        }
    }
    
    manifest_path = os.path.join(base_dir, "dtmin_continuation_packages_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("================================================================================")
    print("DTMIN CONTINUATION PACKAGES PREPARATION COMPLETE (NON-SUBMITTING):")
    print("================================================================================")
    print("Candidate dt_min       : 1.0e-11 s")
    print("Donor Package INP SHA  : %s" % donor_res["dst_inp_sha256"])
    print("Refined Package INP SHA: %s" % ref_res["dst_inp_sha256"])
    print("Subroutine FOR SHA     : %s" % donor_res["dst_for_sha256"])
    print("Manifest saved to      : %s" % manifest_path)

if __name__ == "__main__":
    main()
