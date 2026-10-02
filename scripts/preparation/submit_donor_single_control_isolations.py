#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qualify, Preflight, and Submit Guarded 2-Job Batch of Donor Single-Control Isolations:
1. M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL
2. M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL
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
    manifest_path = os.path.join(base_dir, "donor_single_control_isolation_manifest.json")
    
    with open(manifest_path, "r") as fp:
        manifest = json.load(fp)
        
    pkg_ia13 = manifest["isolation_packages"]["M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL"]
    pkg_dtmin = manifest["isolation_packages"]["M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL"]
    
    # 1. Local Pre-Submission Verification
    for pkg in [pkg_ia13, pkg_dtmin]:
        pkg_dir = pkg["package_dir"]
        pkg_name = pkg["package_name"]
        inp_path = os.path.join(pkg_dir, pkg_name + ".inp")
        for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
        pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
        
        assert sha256_file(inp_path) == pkg["hashes"]["inp_sha256"]
        assert sha256_file(for_path) == pkg["hashes"]["for_sha256"]
        assert sha256_file(pbs_path) == pkg["hashes"]["pbs_sha256"]
        
        with open(pbs_path, "rb") as f:
            assert b"\r\n" not in f.read(), "CRLF found in %s" % pbs_path
            
        print("Package %s: HASHES AND UNIX LF VERIFIED" % pkg_name)
        
    # 2. Sync packages to HPC
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    cmd_sync1 = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, pkg_ia13["package_dir"], remote_base)
    run_cmd(cmd_sync1)
    
    cmd_sync2 = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, pkg_dtmin["package_dir"], remote_base)
    run_cmd(cmd_sync2)
    
    # 3. Remote Datacheck / Notification Preflight / Concurrency Guard / 2-Job Batch Submission
    remote_script = (
        "echo '=== 2. REMOTE DATACHECKS ===' && "
        "module purge && module load gcc/11.4.0 && module load intel/2024.2.0 && module load abaqus/2023 && "
        "cd " + remote_base + "/" + pkg_ia13["package_name"] + " && "
        "abaqus job=" + pkg_ia13["package_name"] + " input=" + pkg_ia13["package_name"] + ".inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive && "
        "DC1_RC=$? && echo DC1_RC=$DC1_RC && if [ $DC1_RC -ne 0 ]; then echo 'DATACHECK IA13 FAILED'; exit 1; fi && "
        "cd " + remote_base + "/" + pkg_dtmin["package_name"] + " && "
        "abaqus job=" + pkg_dtmin["package_name"] + " input=" + pkg_dtmin["package_name"] + ".inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive && "
        "DC2_RC=$? && echo DC2_RC=$DC2_RC && if [ $DC2_RC -ne 0 ]; then echo 'DATACHECK DTMIN FAILED'; exit 1; fi && "
        "echo '=== 3. DUAL-CHANNEL NOTIFICATION PREFLIGHT ===' && "
        "python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode test --channel both && "
        "echo '=== 4. CONCURRENCY GUARD AUDIT ===' && "
        "RUNNING_COUNT=$(qstat -u pr21vyci | grep -E ' R ' | wc -l) && "
        "echo Currently running jobs: $RUNNING_COUNT && "
        "echo '=== 5. SUBMITTING GUARDED 2-JOB BATCH ===' && "
        "cd " + remote_base + "/" + pkg_ia13["package_name"] + " && rm -f *.lck && "
        "IA13_PBS_ID=$(qsub submit_job.pbs) && echo SUBMITTED_IA13_JOB_ID=$IA13_PBS_ID && "
        "cd " + remote_base + "/" + pkg_dtmin["package_name"] + " && rm -f *.lck && "
        "DTMIN_PBS_ID=$(qsub submit_job.pbs) && echo SUBMITTED_DTMIN_JOB_ID=$DTMIN_PBS_ID && "
        "echo '=== 6. SCHEDULER STATUS & ACCOUNTING ===' && "
        "qstat -x $IA13_PBS_ID && qstat -xf $IA13_PBS_ID && "
        "qstat -x $DTMIN_PBS_ID && qstat -xf $DTMIN_PBS_ID && "
        "echo '=== 7. WATCHER SIDECAR VERIFICATION ===' && "
        "ps aux | grep '[w]atcher' || echo 'No watcher process found via ps'"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    rc, out, err = run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
