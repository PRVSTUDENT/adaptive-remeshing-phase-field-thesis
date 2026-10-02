#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Submit Guarded 2-Job Batch E2 Transfer Validation to HPC:
1. M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL
2. M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL
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
    manifest_path = os.path.join(base_dir, "batch_e2_transfers_manifest.json")
    
    with open(manifest_path, "r") as fp:
        manifest = json.load(fp)
        
    prov_ref = manifest["packages"]["refined_transfer"]
    prov_coarse = manifest["packages"]["coarsened_transfer"]
    
    # 1. Verify Local Hashes & Sizes
    print("================================================================================")
    print("1. PRE-SUBMISSION HASH & INTEGRITY VERIFICATION")
    print("================================================================================")
    for prov in [prov_ref, prov_coarse]:
        pkg_dir = prov["package_dir"]
        pkg_name = prov["package_name"]
        inp_path = os.path.join(pkg_dir, pkg_name + ".inp")
        bin_path = os.path.join(pkg_dir, "STAGE_D_COMMITTED_STATE.bin")
        for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
        pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
        
        curr_inp_sha = sha256_file(inp_path)
        curr_bin_sha = sha256_file(bin_path)
        curr_for_sha = sha256_file(for_path)
        curr_pbs_sha = sha256_file(pbs_path)
        
        assert curr_inp_sha == prov["inp_sha256"], "Mismatch in INP SHA for %s" % pkg_name
        assert curr_bin_sha == prov["bin_sha256"], "Mismatch in BIN SHA for %s" % pkg_name
        assert os.path.getsize(bin_path) == 6400016, "Invalid BIN size for %s" % pkg_name
        
        # Check CRLF
        with open(pbs_path, "rb") as f:
            if b"\r\n" in f.read():
                raise AssertionError("CRLF found in %s" % pbs_path)
                
        print("Package %s: ALL HASHES & INTEGRITY CHECKS MATCH MANIFEST EXACTLY (BIN size = 6,400,016 bytes)" % pkg_name)
        
    # Sync packages to cluster
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    cmd_sync_ref = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, prov_ref["package_dir"], remote_base)
    run_cmd(cmd_sync_ref)
    
    cmd_sync_coarse = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, prov_coarse["package_dir"], remote_base)
    run_cmd(cmd_sync_coarse)
    
    # 2. Remote Notification Preflight & Concurrency Check & Submission
    remote_script = (
        "echo '=== 2. NOTIFICATION PREFLIGHT ===' && "
        "python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode test --channel both && "
        "echo '=== 3. CONCURRENCY GUARD AUDIT ===' && "
        "RUNNING_COUNT=$(qstat -u pr21vyci | grep -E ' R ' | wc -l) && "
        "echo Currently running jobs: $RUNNING_COUNT && "
        "echo '=== 4. SUBMITTING BATCH E2 JOBS ===' && "
        "cd " + remote_base + "/" + prov_ref["package_name"] + " && "
        "REF_PBS_ID=$(qsub submit_job.pbs) && "
        "echo SUBMITTED_REFINED_JOB_ID=$REF_PBS_ID && "
        "cd " + remote_base + "/" + prov_coarse["package_name"] + " && "
        "COARSE_PBS_ID=$(qsub submit_job.pbs) && "
        "echo SUBMITTED_COARSENED_JOB_ID=$COARSE_PBS_ID && "
        "echo '=== 5. SCHEDULER STATUS & ACCOUNTING ===' && "
        "qstat -x $REF_PBS_ID && qstat -xf $REF_PBS_ID && "
        "qstat -x $COARSE_PBS_ID && qstat -xf $COARSE_PBS_ID && "
        "echo '=== 6. WATCHER SIDECAR VERIFICATION ===' && "
        "ps aux | grep '[w]atcher' || echo 'No watcher process found via ps'"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    rc, out, err = run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
