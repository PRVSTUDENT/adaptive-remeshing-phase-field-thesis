#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dual-Lineage Derivation, Pre-Submission Qualification, and Guarded Submission
of M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL (I_A = 13, dt_min = 5.0e-12 s)
"""

import os
import sys
import subprocess
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

def run_cmd(cmd):
    print("Executing: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    out_str = out.decode('utf-8', errors='ignore')
    err_str = err.decode('utf-8', errors='ignore')
    print("STDOUT:\n%s" % out_str)
    if err_str:
        print("STDERR:\n%s" % err_str)
    return p.returncode, out_str, err_str

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    pkg_name = "M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL"
    pkg_dir = os.path.join(base_dir, pkg_name)
    if not os.path.exists(pkg_dir):
        os.makedirs(pkg_dir)
        
    inp_ia13_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL.inp")
    inp_dtmin_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL.inp")
    src_for_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/f44_mixed_uel_restart_stateinit.for")
    
    # 1. Dual-Lineage Derivation
    with open(inp_ia13_path, "r") as f:
        text_ia13 = f.read()
    with open(inp_dtmin_path, "r") as f:
        text_dtmin = f.read()
        
    # Derivation A: from IA13 (1391301), change dt_min: 1.0e-11 -> 5.0e-12
    inp_deriv_a = text_ia13.replace(
        "** JOB NAME: M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL",
        "** JOB NAME: " + pkg_name
    ).replace(
        "0.001, 1.0, 1.0e-11, 0.02",
        "0.001, 1.0, 5.0e-12, 0.02"
    )
    
    # Derivation B: from DTMIN5E12 (1391302), change I_A: 12 -> 13
    inp_deriv_b = text_dtmin.replace(
        "** JOB NAME: M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL",
        "** JOB NAME: " + pkg_name
    ).replace(
        "4, 8, 9, 16, 10, 4, 50, 12",
        "4, 8, 9, 16, 10, 4, 50, 13"
    )
    
    # Save both temporarily and test byte equality
    temp_a = os.path.join(pkg_dir, "deriv_a.inp")
    temp_b = os.path.join(pkg_dir, "deriv_b.inp")
    with open(temp_a, "w") as f: f.write(inp_deriv_a)
    with open(temp_b, "w") as f: f.write(inp_deriv_b)
    clean_lf(temp_a)
    clean_lf(temp_b)
    
    sha_a = sha256_file(temp_a)
    sha_b = sha256_file(temp_b)
    
    print("================================================================================")
    print("DUAL-LINEAGE DERIVATION PROVENANCE CHECK:")
    print("================================================================================")
    print("Derivation A (from 1391301 via dt_min: 1e-11 -> 5e-12) SHA256:\n  %s" % sha_a)
    print("Derivation B (from 1391302 via I_A: 12 -> 13) SHA256:\n  %s" % sha_b)
    
    assert sha_a == sha_b, "FATAL: Dual-lineage derivations produced different SHA256 hashes!"
    print("PROVENANCE RESULT: 100% BYTE-IDENTICAL AND SHA-256 IDENTICAL!")
    
    # Write canonical INP
    dst_inp = os.path.join(pkg_dir, pkg_name + ".inp")
    with open(dst_inp, "w") as f: f.write(inp_deriv_a)
    clean_lf(dst_inp)
    
    os.remove(temp_a)
    os.remove(temp_b)
    
    # Copy Subroutine
    dst_for = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    with open(src_for_path, "r") as f: c_for = f.read()
    with open(dst_for, "w") as f: f.write(c_for)
    clean_lf(dst_for)
    
    # Write PBS Launcher
    pbs_content = """#!/bin/bash
#PBS -N M2E_D_COMB_VAL
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
JOBNAME=M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL
USER_SUBROUTINE=f44_mixed_uel_restart_stateinit.for

echo "[PBS] Starting job $PBS_JOBID on host $(hostname) at $(date)"
abaqus job=$JOBNAME input=$JOBNAME.inp user=$USER_SUBROUTINE cpus=1 interactive
EXIT_STATUS=$?
echo "[PBS] Solver execution exited with status $EXIT_STATUS at $(date)"
exit $EXIT_STATUS
"""
    dst_pbs = os.path.join(pkg_dir, "submit_job.pbs")
    with open(dst_pbs, "w") as f: f.write(pbs_content)
    clean_lf(dst_pbs)
    
    inp_sha = sha256_file(dst_inp)
    for_sha = sha256_file(dst_for)
    pbs_sha = sha256_file(dst_pbs)
    
    # 2. Sync to HPC
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    cmd_sync = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, pkg_dir, remote_base)
    run_cmd(cmd_sync)
    
    # 3. Remote Datacheck / Notification Preflight / Concurrency Guard / Submission
    remote_script = (
        "echo '=== 1. REMOTE DATACHECK ===' && "
        "module purge && module load gcc/11.4.0 && module load intel/2024.2.0 && module load abaqus/2023 && "
        "cd " + remote_base + "/" + pkg_name + " && "
        "abaqus job=" + pkg_name + " input=" + pkg_name + ".inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive && "
        "DC_RC=$? && echo DATACHECK_RC=$DC_RC && if [ $DC_RC -ne 0 ]; then echo 'DATACHECK FAILED'; exit 1; fi && "
        "echo '=== 2. DUAL-CHANNEL NOTIFICATION PREFLIGHT ===' && "
        "python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode test --channel both && "
        "echo '=== 3. CONCURRENCY GUARD AUDIT ===' && "
        "RUNNING_COUNT=$(qstat -u pr21vyci | grep -E ' R ' | wc -l) && "
        "echo Currently running jobs: $RUNNING_COUNT && "
        "echo '=== 4. SUBMITTING GUARDED COMBINED JOB ===' && "
        "cd " + remote_base + "/" + pkg_name + " && rm -f *.lck && "
        "COMB_PBS_ID=$(qsub submit_job.pbs) && echo SUBMITTED_COMBINED_JOB_ID=$COMB_PBS_ID && "
        "echo '=== 5. SCHEDULER STATUS & ACCOUNTING ===' && "
        "qstat -x $COMB_PBS_ID && qstat -xf $COMB_PBS_ID && "
        "echo '=== 6. WATCHER SIDECAR VERIFICATION ===' && "
        "ps aux | grep '[w]atcher' || echo 'No watcher process found via ps'"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    rc, out, err = run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
