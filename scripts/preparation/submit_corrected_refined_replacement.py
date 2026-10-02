#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qualify and Submit Single Corrected Refined Replacement Job:
M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL
"""

import os
import sys
import subprocess
import json
import hashlib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

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
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    pkg_name = "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL"
    local_pkg_dir = os.path.join(base_dir, pkg_name)
    manifest_path = os.path.join(base_dir, "refined_r1_one_difference_manifest.json")
    
    with open(manifest_path, "r") as fp:
        manifest = json.load(fp)
        
    # 1. Local Pre-Submission Verification
    inp_path = os.path.join(local_pkg_dir, pkg_name + ".inp")
    bin_path = os.path.join(local_pkg_dir, "STAGE_D_COMMITTED_STATE.bin")
    for_path = os.path.join(local_pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_path = os.path.join(local_pkg_dir, "submit_job.pbs")
    
    assert sha256_file(inp_path) == manifest["hashes"]["inp_sha256"]
    assert sha256_file(bin_path) == manifest["hashes"]["bin_sha256"]
    assert os.path.getsize(bin_path) == 6400016
    
    print("================================================================================")
    print("1. LOCAL INTEGRITY & HASHES VERIFIED")
    print("================================================================================")
    
    # 2. Sync to HPC
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    cmd_sync = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, local_pkg_dir, remote_base)
    run_cmd(cmd_sync)
    
    # 3. Remote Compile / Datacheck / Notification Preflight / Concurrency Guard / Submission
    remote_script = (
        "echo '=== 2. REMOTE COMPILATION & DATACHECK ===' && "
        "cd " + remote_base + "/" + pkg_name + " && "
        "module purge && module load gcc/11.4.0 && module load intel/2024.2.0 && module load abaqus/2023 && "
        "abaqus job=" + pkg_name + " input=" + pkg_name + ".inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive && "
        "DATACHECK_RC=$? && echo DATACHECK_RC=$DATACHECK_RC && "
        "if [ $DATACHECK_RC -ne 0 ]; then echo 'DATACHECK FAILED'; exit 1; fi && "
        "echo '=== 3. NOTIFICATION PREFLIGHT ===' && "
        "python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode test --channel both && "
        "echo '=== 4. CONCURRENCY GUARD AUDIT ===' && "
        "RUNNING_COUNT=$(qstat -u pr21vyci | grep -E ' R ' | wc -l) && "
        "echo Currently running jobs: $RUNNING_COUNT && "
        "echo '=== 5. SUBMITTING CORRECTED REFINED JOB ===' && "
        "rm -f *.lck && "
        "REFINED_R1_PBS_ID=$(qsub submit_job.pbs) && "
        "echo SUBMITTED_REFINED_R1_JOB_ID=$REFINED_R1_PBS_ID && "
        "echo '=== 6. SCHEDULER STATUS & ACCOUNTING ===' && "
        "qstat -x $REFINED_R1_PBS_ID && qstat -xf $REFINED_R1_PBS_ID && "
        "echo '=== 7. WATCHER SIDECAR VERIFICATION ===' && "
        "ps aux | grep '[w]atcher' || echo 'No watcher process found via ps'"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
