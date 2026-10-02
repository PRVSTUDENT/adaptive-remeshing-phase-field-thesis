#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieve Terminal Artifacts for Batch E2 Jobs 1391281 and 1391282
"""

import os
import sys
import subprocess

def run_cmd(cmd):
    print("Executing: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print("STDOUT:\n%s" % out.decode('utf-8', errors='ignore'))
    if err:
        print("STDERR:\n%s" % err.decode('utf-8', errors='ignore'))
    return p.returncode

def main():
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    local_base = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Sync Refined Transfer Artifacts
    pkg_ref = "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL"
    local_ref_dir = os.path.join(local_base, pkg_ref)
    cmd_sync_ref = "scp -F \"%s\" -r tu_freiberg:%s/%s/* \"%s\"/" % (ssh_cfg, remote_base, pkg_ref, local_ref_dir)
    run_cmd(cmd_sync_ref)
    
    # 2. Sync Coarsened Transfer Artifacts
    pkg_coarse = "M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL"
    local_coarse_dir = os.path.join(local_base, pkg_coarse)
    cmd_sync_coarse = "scp -F \"%s\" -r tu_freiberg:%s/%s/* \"%s\"/" % (ssh_cfg, remote_base, pkg_coarse, local_coarse_dir)
    run_cmd(cmd_sync_coarse)
    
    print("Artifact retrieval completed.")

if __name__ == "__main__":
    main()
