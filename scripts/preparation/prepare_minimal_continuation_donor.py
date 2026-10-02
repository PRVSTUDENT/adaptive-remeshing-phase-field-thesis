#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare and Qualify Package: M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL
Isolating I_A=12 against historical donor control 1390447.mmaster02.
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

def main():
    src_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    dst_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL"
    
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    src_inp = os.path.join(src_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp")
    dst_inp = os.path.join(dst_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.inp")
    
    with open(src_inp, "r") as fp:
        lines = fp.readlines()
        
    new_lines = []
    in_step = False
    controls_inserted = False
    
    for i, line in enumerate(lines):
        # Update heading
        if "*HEADING" in line.upper():
            new_lines.append(line)
            # Replace comment title line if next
            if i + 1 < len(lines) and not lines[i+1].startswith("*"):
                continue # handled below
            continue
        elif i > 0 and "*HEADING" in lines[i-1].upper() and not line.startswith("*"):
            new_lines.append("** Job: M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL (I_A=12 Qualification)\n")
            continue
            
        if "*STATIC" in line.upper():
            new_lines.append(line)
            # Preserve exact *STATIC line 2: 0.001, 1.0, 1.0e-9, 0.02
            continue
            
        if "*STEP" in line.upper():
            in_step = True
            new_lines.append(line)
            continue
            
        # Insert *CONTROLS block right after *STATIC data line
        if in_step and not controls_inserted and i > 0 and "*STATIC" in lines[i-1].upper():
            new_lines.append(line) # this is the static data line: 0.001, 1.0, 1.0e-9, 0.02
            new_lines.append("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
            new_lines.append("4, 8, 9, 16, 10, 4, 50, 12\n")
            controls_inserted = True
            continue
            
        new_lines.append(line)
        
    with open(dst_inp, "w") as fp:
        fp.writelines(new_lines)
        
    print("Generated: %s" % dst_inp)
    
    # Copy Fortran source
    src_for = os.path.join(src_dir, "f44_mixed_uel_restart_stateinit.for")
    dst_for = os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for")
    shutil.copyfile(src_for, dst_for)
    
    # Generate submit_job.pbs
    pbs_content = """#!/bin/bash
#PBS -N M2CORR_STAGE_E_
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -o pbs.out
#PBS -e pbs.err
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail

cd "${PBS_O_WORKDIR}"

# Clean old lock / lck files
rm -f *.lck

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

JOB_NAME="M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL"

abaqus job="${JOB_NAME}" input="${JOB_NAME}.inp" user="f44_mixed_uel_restart_stateinit.for" double=both cpus=1 interactive
"""
    dst_pbs = os.path.join(dst_dir, "submit_job.pbs")
    with open(dst_pbs, "w") as fp:
        fp.write(pbs_content)
        
    print("Generated: %s" % dst_pbs)
    
    # Manifest verification
    sha_src_inp = get_file_sha256(src_inp)
    sha_dst_inp = get_file_sha256(dst_inp)
    sha_src_for = get_file_sha256(src_for)
    sha_dst_for = get_file_sha256(dst_for)
    
    print("\nPackage Verification:")
    print("  FOR Source SHA-256 Identical: %s (%s)" % (sha_src_for == sha_dst_for, sha_dst_for))
    print("  Historical INP SHA-256      : %s" % sha_src_inp)
    print("  New INP SHA-256             : %s" % sha_dst_inp)
    
    # Check diff lines between src_inp and dst_inp
    with open(src_inp, "r") as fp:
        lines_src = fp.readlines()
    with open(dst_inp, "r") as fp:
        lines_dst = fp.readlines()
        
    print("\nLine-by-Line INP Differences:")
    diff_count = 0
    for i, (l1, l2) in enumerate(zip(lines_src, lines_dst)):
        if l1 != l2:
            print("  Line %d diff:\n    SRC: %s    DST: %s" % (i+1, l1.strip(), l2.strip()))
            diff_count += 1
            if diff_count > 10: break
    print("  Length SRC: %d, Length DST: %d (Diff: +%d lines for *CONTROLS block)" % (
        len(lines_src), len(lines_dst), len(lines_dst) - len(lines_src)))

if __name__ == "__main__":
    main()
