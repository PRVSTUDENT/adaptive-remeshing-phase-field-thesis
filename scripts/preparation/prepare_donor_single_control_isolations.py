#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare Two Single-Control Donor Isolation Packages:
1. M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL (I_A: 12 -> 13, dt_min = 1.0e-11)
2. M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL (dt_min: 1.0e-11 -> 5.0e-12, I_A = 12)
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
            if not chunk: break
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
    src_dir = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL")
    src_inp = os.path.join(src_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    src_for = os.path.join(src_dir, "f44_mixed_uel_restart_stateinit.for")
    
    with open(src_inp, "r") as f:
        base_inp_content = f.read()
        
    packages = [
        {
            "pkg_name": "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL",
            "job_pbs_name": "M2E_D_IA13_ISO",
            "modified_static": "0.001, 1.0, 1.0e-11, 0.02",
            "modified_controls": "4, 8, 9, 16, 10, 4, 50, 13",
            "change_desc": "I_A: 12 -> 13 with dt_min = 1.0e-11 unchanged",
            "param_diff": {"I_A": [12, 13], "dt_min": ["1.0e-11", "1.0e-11"]}
        },
        {
            "pkg_name": "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL",
            "job_pbs_name": "M2E_D_DT5E12_ISO",
            "modified_static": "0.001, 1.0, 5.0e-12, 0.02",
            "modified_controls": "4, 8, 9, 16, 10, 4, 50, 12",
            "change_desc": "dt_min: 1.0e-11 -> 5.0e-12 with I_A = 12 unchanged",
            "param_diff": {"I_A": [12, 12], "dt_min": ["1.0e-11", "5.0e-12"]}
        }
    ]
    
    manifest_records = {}
    
    for pkg in packages:
        pkg_name = pkg["pkg_name"]
        dst_dir = os.path.join(base_dir, pkg_name)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
            
        # Copy UEL subroutine
        dst_for = os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for")
        shutil.copy2(src_for, dst_for)
        clean_lf(dst_for)
        
        # Build INP
        target_static_line = "0.001, 1.0, 1.0e-11, 0.02"
        target_controls_line = "4, 8, 9, 16, 10, 4, 50, 12"
        
        assert target_static_line in base_inp_content
        assert target_controls_line in base_inp_content
        
        inp_content = base_inp_content.replace(
            "** JOB NAME: M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
            "** JOB NAME: " + pkg_name
        ).replace(
            target_static_line,
            pkg["modified_static"]
        ).replace(
            target_controls_line,
            pkg["modified_controls"]
        )
        
        dst_inp = os.path.join(dst_dir, pkg_name + ".inp")
        with open(dst_inp, "w") as f:
            f.write(inp_content)
        clean_lf(dst_inp)
        
        # Build PBS launcher
        pbs_content = """#!/bin/bash
#PBS -N %(pbs_name)s
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
JOBNAME=%(pkg_name)s
USER_SUBROUTINE=f44_mixed_uel_restart_stateinit.for

echo "[PBS] Starting job $PBS_JOBID on host $(hostname) at $(date)"
abaqus job=$JOBNAME input=$JOBNAME.inp user=$USER_SUBROUTINE cpus=1 interactive
EXIT_STATUS=$?
echo "[PBS] Solver execution exited with status $EXIT_STATUS at $(date)"
exit $EXIT_STATUS
""" % {"pbs_name": pkg["job_pbs_name"], "pkg_name": pkg_name}
        
        dst_pbs = os.path.join(dst_dir, "submit_job.pbs")
        with open(dst_pbs, "w") as f:
            f.write(pbs_content)
        clean_lf(dst_pbs)
        
        # Manifest entry
        inp_sha = sha256_file(dst_inp)
        for_sha = sha256_file(dst_for)
        pbs_sha = sha256_file(dst_pbs)
        
        # Compute unified diff
        with open(src_inp, "r") as f1, open(dst_inp, "r") as f2:
            udiff = list(difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile="1390876_donor", tofile=pkg_name))
            
        manifest_records[pkg_name] = {
            "package_name": pkg_name,
            "package_dir": dst_dir,
            "base_job": "1390876.mmaster02",
            "base_package": "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
            "change_description": pkg["change_desc"],
            "parameter_diff": pkg["param_diff"],
            "hashes": {
                "inp_sha256": inp_sha,
                "for_sha256": for_sha,
                "pbs_sha256": pbs_sha
            },
            "unified_diff": [line.rstrip() for line in udiff]
        }
        
        print("================================================================================")
        print("PACKAGE: %s" % pkg_name)
        print("INP SHA256: %s" % inp_sha)
        print("FOR SHA256: %s" % for_sha)
        print("UNIFIED DIFF:")
        for line in udiff:
            print("  " + line.rstrip())
            
    out_manifest = os.path.join(base_dir, "donor_single_control_isolation_manifest.json")
    with open(out_manifest, "w") as fp:
        json.dump({"isolation_packages": manifest_records}, fp, indent=2)
    print("\nSaved Isolation Manifest to: %s" % out_manifest)

if __name__ == "__main__":
    main()
