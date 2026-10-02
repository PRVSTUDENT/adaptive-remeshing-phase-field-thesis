#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Execute remote datachecks on cluster via direct bash command string
"""
import os
import sys
import subprocess

def main():
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    
    remote_cmd = (
        "module purge && module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 && "
        "cd /home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL && "
        "rm -f *.lck *.log *.dat *.msg *.sta *.prt && "
        "abaqus job=M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL input=M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL.inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive && "
        "echo REFINED_RC=$? && "
        "cd /home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL && "
        "rm -f *.lck *.log *.dat *.msg *.sta *.prt && "
        "abaqus job=M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL input=M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL.inp user=f44_mixed_uel_restart_stateinit.for datacheck interactive && "
        "echo COARSENED_RC=$?"
    )
    
    full_cmd = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_cmd)
    print("Executing remote command...")
    p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print("STDOUT:\n%s" % out.decode('utf-8', errors='ignore'))
    if err:
        print("STDERR:\n%s" % err.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    main()
