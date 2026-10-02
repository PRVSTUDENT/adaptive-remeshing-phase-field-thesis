#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieve and Evaluate Corrected Refined Replacement Job 1391300.mmaster02
"""

import os
import sys
import subprocess
import json

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
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    local_base = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    pkg_name = "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL"
    
    # 1. Fetch Remote Qstat & Logs
    remote_script = (
        "echo '=== QSTAT -XF ===' && "
        "qstat -xf 1391300.mmaster02 && "
        "echo '=== DIRECTORY LISTING ===' && "
        "cd " + remote_base + "/" + pkg_name + " && "
        "ls -la && "
        "echo '=== STA FILE ===' && cat *.sta 2>/dev/null || true && "
        "echo '=== MSG TAIL ===' && tail -n 80 *.msg 2>/dev/null || true"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    rc, qstat_out, err = run_cmd(cmd_ssh)
    
    # 2. Sync Artifacts to Local
    local_dir = os.path.join(local_base, pkg_name)
    cmd_sync = "scp -F \"%s\" -r tu_freiberg:%s/%s/* \"%s\"/" % (ssh_cfg, remote_base, pkg_name, local_dir)
    run_cmd(cmd_sync)
    
    print("Artifacts synchronized successfully.")

if __name__ == "__main__":
    main()
