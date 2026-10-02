#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build Stage-E Triplet Continuous Baseline Packages with Frozen Continuation Protocol:
1. M2CORR_STAGE_E_DONOR_CONTROL_VAL (8,836 quads, h_tip=0.003750 mm)
2. M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL (33,600 quads, h_tip=0.002000 mm)
3. M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL (8,200 quads, h_tip=0.005000 mm)

Frozen Continuation Protocol:
- *CONTROLS, PARAMETERS=TIME INCREMENTATION:
  Line 1: 8, 10, 9, 20, 10, 4, 50, 12 (I_0=8, I_R=10, I_P=9, I_C=20, I_L=10, I_G=4, I_S=50, I_A=12)
  Line 2: 0.25, 0.5, 0.75, 0.25, 0.25, 1.5, 1.5, 1.25
- *STATIC: 0.001, 1.0, 1.0e-10, 0.02
- Two-layer UEL formulation (E_QUAD_PHASE on U1 DOF 3, E_QUAD_MECH on U2 DOFs 1,2)
- PROPS: (0.015, 0.0027, 210.0, 0.3, 1e-7, N_PHYS, 0.0) in Virgin Continuous Mode
- Shear-only top *EQUATION coupling to RP 99999
"""

import os
import sys
import json
import shutil
import hashlib
import numpy as np

def update_inp_with_continuation_controls(inp_path):
    with open(inp_path, "r") as fp:
        lines = fp.readlines()
        
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("*STATIC"):
            out_lines.append(line)
            out_lines.append("0.001, 1.0, 1.0e-10, 0.02\n")
            out_lines.append("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
            out_lines.append("8, 10, 9, 20, 10, 4, 50, 12\n")
            out_lines.append("0.25, 0.50, 0.75, 0.25, 0.25, 1.5, 1.5, 1.25\n")
            # Skip old static params and any old controls block
            i += 2
            while i < len(lines) and (lines[i].strip().startswith("*CONTROLS") or lines[i].strip().startswith(",") or lines[i].strip().startswith("8,") or lines[i].strip().startswith("0.25,")):
                i += 1
            continue
        elif line.strip().startswith("*CONTROLS"):
            # Skip legacy controls
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("*"):
                i += 1
            continue
        else:
            out_lines.append(line)
            i += 1
            
    with open(inp_path, "w", newline="\n") as fp:
        fp.writelines(out_lines)

def build_triplet_packages():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    donor_src_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    
    packages = [
        ("M2CORR_STAGE_E_DONOR_CONTROL_VAL", donor_src_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp", 8836),
        ("M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL", os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL"), "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp", 33600),
        ("M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL", os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL"), "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp", 8200)
    ]
    
    for pkg_name, src_dir, inp_name, num_quads in packages:
        pkg_dir = os.path.join(base_dir, pkg_name)
        os.makedirs(pkg_dir, exist_ok=True)
        
        # Target files
        tgt_inp = os.path.join(pkg_dir, "%s.inp" % pkg_name)
        tgt_for = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
        tgt_pbs = os.path.join(pkg_dir, "submit_job.pbs")
        
        # Copy source INP if donor
        if pkg_name == "M2CORR_STAGE_E_DONOR_CONTROL_VAL":
            shutil.copy2(os.path.join(src_dir, inp_name), tgt_inp)
            # Update heading
            with open(tgt_inp, "r") as fp:
                inp_content = fp.read()
            inp_content = inp_content.replace("M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL", "M2CORR_STAGE_E_DONOR_CONTROL_VAL")
            with open(tgt_inp, "w", newline="\n") as fp:
                fp.write(inp_content)
                
        # Copy UEL subroutine
        uel_src = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/f44_mixed_uel_restart_stateinit.for"
        shutil.copy2(uel_src, tgt_for)
        
        # Apply continuation controls
        update_inp_with_continuation_controls(tgt_inp)
        
        # Write PBS script
        with open(tgt_pbs, "w", newline="\n") as fp:
            fp.write("#!/bin/bash\n")
            fp.write("#PBS -N %s\n" % pkg_name[:15])
            fp.write("#PBS -l select=1:ncpus=1:mem=16gb\n")
            fp.write("#PBS -l walltime=24:00:00\n")
            fp.write("#PBS -q entry_imfdfkmq\n")
            fp.write("#PBS -m abe\n")
            fp.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n")
            fp.write("#PBS -o pbs.out\n")
            fp.write("#PBS -e pbs.err\n\n")
            fp.write("cd $PBS_O_WORKDIR\n\n")
            fp.write("module purge\n")
            fp.write("module load gcc/11.4.0\n")
            fp.write("module load intel/2024.2.0\n")
            fp.write("module load abaqus/2023\n\n")
            fp.write("echo \"Job started on $(hostname) at $(date)\"\n\n")
            fp.write("abaqus job=%s input=%s.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive\n" % (pkg_name, pkg_name))
            fp.write("ABAQUS_RC=$?\n\n")
            fp.write("echo \"Abaqus finished with return code ${ABAQUS_RC} at $(date)\"\n\n")
            fp.write("exit ${ABAQUS_RC}\n")
            
        # Clean obsolete output files in pkg_dir
        for f in os.listdir(pkg_dir):
            if f.endswith(('.odb', '.sta', '.msg', '.dat', '.prt', '.com', '.env', '.csv', '.lck')):
                try: os.remove(os.path.join(pkg_dir, f))
                except: pass
                
        # Generate manifest
        manifest = {}
        for f_k in sorted(os.listdir(pkg_dir)):
            p_k = os.path.join(pkg_dir, f_k)
            if os.path.isfile(p_k) and f_k != "manifest.json":
                with open(p_k, "rb") as fp_k:
                    manifest[f_k] = hashlib.sha256(fp_k.read()).hexdigest()
        with open(os.path.join(pkg_dir, "manifest.json"), "w", newline="\n") as fp_m:
            json.dump(manifest, fp_m, indent=2)
            
        print("Built package %s in %s" % (pkg_name, pkg_dir))
        print("  INP SHA-256: %s" % manifest["%s.inp" % pkg_name])

if __name__ == "__main__":
    build_triplet_packages()
