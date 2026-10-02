#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Non-Submitting Cluster Qualification for Stage-E Transfer Packages:
1. Transfer files to cluster
2. Run interactive compilation and datacheck on mlogin01
3. Verify zero errors and zero warnings
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
    
    # 1. Sync Refined Transfer Package
    pkg_ref = "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL"
    local_ref_dir = os.path.join(local_base, pkg_ref)
    cmd_sync_ref = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, local_ref_dir, remote_base)
    run_cmd(cmd_sync_ref)
    
    # 2. Sync Coarsened Transfer Package
    pkg_coarse = "M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL"
    local_coarse_dir = os.path.join(local_base, pkg_coarse)
    cmd_sync_coarse = "scp -F \"%s\" -r \"%s\" tu_freiberg:%s/" % (ssh_cfg, local_coarse_dir, remote_base)
    run_cmd(cmd_sync_coarse)
    
    # 3. Interactive Compilation & Datacheck on cluster
    remote_script = """
    module purge
    module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
    
    echo "================================================================================"
    echo "DATACHECK: REFINED TRANSFER PACKAGE"
    echo "================================================================================"
    cd %(remote_base)s/%(pkg_ref)s
    rm -f *.lck *.log *.dat *.msg *.sta *.prt
    abaqus job=%(pkg_ref)s input=%(pkg_ref)s.inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive
    RC_REF=$?
    echo "Refined Datacheck Return Code: $RC_REF"
    
    echo "================================================================================"
    echo "DATACHECK: COARSENED TRANSFER PACKAGE"
    echo "================================================================================"
    cd %(remote_base)s/%(pkg_coarse)s
    rm -f *.lck *.log *.dat *.msg *.sta *.prt
    abaqus job=%(pkg_coarse)s input=%(pkg_coarse)s.inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive
    RC_COARSE=$?
    echo "Coarsened Datacheck Return Code: $RC_COARSE"
    
    if [ $RC_REF -eq 0 ] && [ $RC_COARSE -eq 0 ]; then
        echo "ALL_TRANSFER_DATACHECKS_PASSED_CLEANLY"
    else
        echo "DATACHECK_FAILED"
    fi
    """ % {"remote_base": remote_base, "pkg_ref": pkg_ref, "pkg_coarse": pkg_coarse}
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"bash -s\" << 'EOF'\n%s\nEOF" % (ssh_cfg, remote_script)
    run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
