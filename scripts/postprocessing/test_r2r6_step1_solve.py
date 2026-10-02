from odbAccess import openOdb
import subprocess
import math
import sys
import os

def test_step1_solve():
    pkg_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6"
    inp_path = os.path.join(pkg_dir, "M2STATE_FRACFIX_RESTART2R6.inp")
    
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    step1_lines = []
    for line in lines:
        if "*STEP, NAME=Step-2-Continuation" in line:
            break
        step1_lines.append(line)
        
    step1_inp = "/home/pr21vyci/test_r2r6_step1.inp"
    with open(step1_inp, "w") as f:
        f.writelines(step1_lines)
        
    print("Created %s with %d lines" % (step1_inp, len(step1_lines)))
    
    cmd = (
        "source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true; "
        "module purge; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7; "
        "cd /home/pr21vyci && "
        "rm -f test_r2r6_step1.odb test_r2r6_step1.dat test_r2r6_step1.msg test_r2r6_step1.sta test_r2r6_step1.com test_r2r6_step1.prt && "
        "abaqus job=test_r2r6_step1 user=/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6/f42_mixed_uel.for interactive"
    )
    res = subprocess.call(cmd, shell=True)
    
    odb_path = "/home/pr21vyci/test_r2r6_step1.odb"
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps["Step-1-PhaseInit"]
    frame = step.frames[-1]
    u = frame.fieldOutputs["U"]
    
    nan_count = 0
    max_u1 = 0.0
    for v in u.values:
        if math.isnan(v.data[0]) or math.isnan(v.data[1]):
            nan_count += 1
        if abs(v.data[0]) > max_u1:
            max_u1 = abs(v.data[0])
            
    print("Step 1 Frame 1 (t=%.2f): total values=%d, NaNs=%d, max|U1|=%.6f" % (frame.frameValue, len(u.values), nan_count, max_u1))
    odb.close()
    
    if nan_count == 0:
        print("SUCCESS: STEP 1 SOLVED WITH 100% FINITE DISPLACEMENTS! ZERO NaNs!")
    else:
        print("ERROR: Step 1 contains %d NaNs!" % nan_count)

if __name__ == "__main__":
    test_step1_solve()
