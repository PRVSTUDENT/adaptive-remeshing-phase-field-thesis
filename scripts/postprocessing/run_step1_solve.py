#!/usr/bin/env python3
import os
import subprocess

def run_step1():
    pkg_inp = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6/M2STATE_FRACFIX_RESTART2R6.inp"
    with open(pkg_inp, "r") as f:
        lines = f.readlines()
        
    step1_lines = []
    for line in lines:
        if "*STEP, NAME=Step-2-Continuation" in line:
            break
        step1_lines.append(line)
        
    out_inp = "/home/pr21vyci/test_r2r6_step1.inp"
    with open(out_inp, "w") as f:
        f.writelines(step1_lines)
        
    print(f"Wrote {out_inp} with {len(step1_lines)} lines")
    
    # Remove old solver outputs
    for ext in [".odb", ".dat", ".msg", ".sta", ".com", ".prt", ".log"]:
        f = f"/home/pr21vyci/test_r2r6_step1{ext}"
        if os.path.exists(f):
            os.remove(f)
            
    cmd = (
        "source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true; "
        "module purge; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7; "
        "cd /home/pr21vyci && "
        "abaqus job=test_r2r6_step1 user=/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6/f42_mixed_uel.for interactive"
    )
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print(res.stdout)

if __name__ == "__main__":
    run_step1()
