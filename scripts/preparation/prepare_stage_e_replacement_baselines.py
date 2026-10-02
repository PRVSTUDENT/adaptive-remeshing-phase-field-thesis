#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare and Qualify Replacement Continuous E1 Baselines:
1. M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL (from Refined baseline 1390527)
2. M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL (from Coarsened baseline 1390528)
Isolating I_A: 5 -> 12 with all other defaults strictly preserved.
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

def prepare_package(src_dir, src_inp_name, dst_dir, job_name):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    src_inp = os.path.join(src_dir, src_inp_name)
    dst_inp = os.path.join(dst_dir, job_name + ".inp")
    
    with open(src_inp, "r") as fp:
        lines = fp.readlines()
        
    new_lines = []
    in_step = False
    skip_controls = False
    
    for i, line in enumerate(lines):
        # Update heading
        if "*HEADING" in line.upper():
            new_lines.append(line)
            continue
        elif i > 0 and "*HEADING" in lines[i-1].upper() and not line.startswith("*"):
            new_lines.append("** Job: %s (I_A=12 Minimal Continuation Qualification)\n" % job_name)
            continue
            
        if "*STEP" in line.upper():
            in_step = True
            new_lines.append(line)
            continue
            
        if in_step and "*STATIC" in line.upper():
            new_lines.append(line)
            # Enforce exact historical *STATIC line 2: 0.001, 1.0, 1.0e-9, 0.02
            new_lines.append("0.001, 1.0, 1.0e-9, 0.02\n")
            # Insert minimal continuation *CONTROLS block
            new_lines.append("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
            new_lines.append("4, 8, 9, 16, 10, 4, 50, 12\n")
            continue
            
        # Skip old static data line or existing *CONTROLS lines if present
        if in_step and i > 0 and "*STATIC" in lines[i-1].upper():
            continue # already handled above
            
        if in_step and "*CONTROLS" in line.upper():
            skip_controls = True
            continue
            
        if skip_controls:
            # Skip control data lines until next keyword
            if line.strip().startswith("*"):
                skip_controls = False
                new_lines.append(line)
            continue
            
        new_lines.append(line)
        
    with open(dst_inp, "w") as fp:
        fp.writelines(new_lines)
        
    # Copy Fortran source
    src_for = os.path.join(src_dir, "f44_mixed_uel_restart_stateinit.for")
    dst_for = os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for")
    shutil.copyfile(src_for, dst_for)
    
    # Generate submit_job.pbs
    pbs_content = """#!/bin/bash
#PBS -N M2CORR_STAGE_E_
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR

# Clean old lock files
rm -f *.lck

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "Job started on $(hostname) at $(date)"

abaqus job=%s input=%s.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive
ABAQUS_RC=$?

echo "Abaqus finished with return code ${ABAQUS_RC} at $(date)"

exit ${ABAQUS_RC}
""" % (job_name, job_name)

    dst_pbs = os.path.join(dst_dir, "submit_job.pbs")
    with open(dst_pbs, "w") as fp:
        fp.write(pbs_content)
        
    return {
        "job_name": job_name,
        "inp_path": dst_inp,
        "inp_sha256": get_file_sha256(dst_inp),
        "for_sha256": get_file_sha256(dst_for),
        "pbs_path": dst_pbs
    }

def main():
    base_src_refined = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL"
    base_src_coarsened = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL"
    
    base_dst_refined = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL"
    base_dst_coarsened = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL"
    
    res_refined = prepare_package(base_src_refined, "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp",
                                  base_dst_refined, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL")
                                  
    res_coarsened = prepare_package(base_src_coarsened, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp",
                                    base_dst_coarsened, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL")
                                    
    manifest = {
        "refined_replacement": res_refined,
        "coarsened_replacement": res_coarsened,
        "governing_controls": {
            "I_0": 4,
            "I_R": 8,
            "I_P": 9,
            "I_C": 16,
            "I_L": 10,
            "I_G": 4,
            "I_S": 50,
            "I_A": 12,
            "dt_min": 1.0e-9,
            "line_2_overrides": "omitted (defaults preserved)"
        }
    }
    
    out_manifest = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/replacement_baselines_manifest.json"
    with open(out_manifest, "w") as fp:
        json.dump(manifest, fp, indent=2)
        
    print("================================================================================")
    print("REPLACEMENT STAGE-E BASELINE PACKAGES GENERATED:")
    print("================================================================================")
    print("1. Refined Replacement  : %s" % res_refined["inp_path"])
    print("   INP SHA-256          : %s" % res_refined["inp_sha256"])
    print("   FOR SHA-256          : %s" % res_refined["for_sha256"])
    print("2. Coarsened Replacement: %s" % res_coarsened["inp_path"])
    print("   INP SHA-256          : %s" % res_coarsened["inp_sha256"])
    print("   FOR SHA-256          : %s" % res_coarsened["for_sha256"])
    print("Manifest written to     : %s" % out_manifest)

if __name__ == "__main__":
    main()
