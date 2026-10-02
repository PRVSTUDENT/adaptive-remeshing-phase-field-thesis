#!/usr/bin/env python3
import os
import subprocess
import sys

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"

check_script = """from odbAccess import openOdb
import numpy as np

odb = openOdb('STEP1_SOLVE.odb', readOnly=True)
step1 = odb.steps['Step-1-PhaseInit']
frame = step1.frames[-1]
u_field = frame.fieldOutputs['U']

u_vals = [v.data for v in u_field.values]
u_arr = np.array(u_vals)
print 'Field U shape:', u_arr.shape
print 'NaN count:', np.isnan(u_arr).sum()
print 'Inf count:', np.isinf(u_arr).sum()
print 'U1 min/max:', u_arr[:,0].min(), u_arr[:,0].max()
print 'U2 min/max:', u_arr[:,1].min(), u_arr[:,1].max()
if u_arr.shape[1] >= 3:
    print 'U3 (Phase) min/max:', u_arr[:,2].min(), u_arr[:,2].max()
odb.close()
"""

remote_cmd = (
    f"source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
    f"module purge && "
    f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
    f"cd {REMOTE_CANDIDATE} && "
    f"python3 -c \"open('check_step1_odb.py', 'w').write('''{check_script}''')\" && "
    f"abaqus python check_step1_odb.py"
)

cmd = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, remote_cmd]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
