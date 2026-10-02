#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect Remote PBS Logs and Solver Diagnostics for Batch E2
"""
import os
import subprocess

def run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print("STDOUT:\n%s" % out.decode('utf-8', errors='ignore'))
    if err:
        print("STDERR:\n%s" % err.decode('utf-8', errors='ignore'))

def main():
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    remote_script = (
        "echo '========================================================================' && "
        "echo '=== 1391281.mmaster02: REFINED TRANSFER LOGS ===' && "
        "echo '========================================================================' && "
        "cd " + remote_base + "/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL && "
        "ls -la && "
        "echo '--- pbs.out ---' && cat pbs.out 2>/dev/null || true && "
        "echo '--- pbs.err ---' && cat pbs.err 2>/dev/null || true && "
        "echo '--- sta file ---' && cat *.sta 2>/dev/null || true && "
        "echo '--- msg tail ---' && tail -n 50 *.msg 2>/dev/null || true && "
        "echo '========================================================================' && "
        "echo '=== 1391282.mmaster02: COARSENED TRANSFER LOGS ===' && "
        "echo '========================================================================' && "
        "cd " + remote_base + "/M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL && "
        "ls -la && "
        "echo '--- pbs.out ---' && cat pbs.out 2>/dev/null || true && "
        "echo '--- pbs.err ---' && cat pbs.err 2>/dev/null || true && "
        "echo '--- sta file ---' && cat *.sta 2>/dev/null || true && "
        "echo '--- msg tail ---' && tail -n 50 *.msg 2>/dev/null || true"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
