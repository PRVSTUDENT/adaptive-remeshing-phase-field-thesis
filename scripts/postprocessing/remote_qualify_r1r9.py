#!/usr/bin/env python3
"""
Remote Qualification Script for Candidate M2STATE_FRACFIX_RESTART1R1R9.
Task ID: F91STATE-M2-INSTRUMENTED-RESTART1-R1R9-PREP-AND-QUALIFICATION1
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9"

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9'
    remote_test_file = '/home/pr21vyci/projects/adaptive-remeshing/tests/unit/test_m2state_fracfix_restart1r1r9.py'

    print("=== 1. SYNCING PACKAGE TO CLUSTER ===")
    ssh_mkdir = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, f'mkdir -p {remote_pkg_dir}']
    subprocess.run(ssh_mkdir, check=True)

    files_to_sync = [
        "M2STATE_FRACFIX_RESTART1R1R9.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R9.pbs",
        "submit_m2state_fracfix_restart1r1r9.sh",
        "PACKAGE_MANIFEST.json"
    ]

    for fn in files_to_sync:
        local_p = LOCAL_PKG_DIR / fn
        scp_cmd = ['scp', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', str(local_p), f'{host}:{remote_pkg_dir}/{fn}']
        subprocess.run(scp_cmd, check=True)

    # Sync test file
    local_test_p = ROOT / "tests/unit/test_m2state_fracfix_restart1r1r9.py"
    scp_test = ['scp', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', str(local_test_p), f'{host}:{remote_test_file}']
    subprocess.run(scp_test, check=True)

    print("=== 2. RUNNING REMOTE VALIDATION, DATACHECK, AND STEP-1 SOLVE ===")
    remote_script = f"""#!/bin/bash
set -e
export XDG_RUNTIME_DIR=/tmp/pr21vyci-runtime
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

cd /home/pr21vyci/projects/adaptive-remeshing

echo "=== A. MANIFEST PREFLIGHT ==="
cd "{remote_pkg_dir}"
python3 validate_package_manifest.py

echo "=== B. RUNNING PYTEST ==="
cd /home/pr21vyci/projects/adaptive-remeshing
pytest tests/unit/test_m2state_fracfix_restart1r1r9.py -v

echo "=== C. LOADING MODULES ==="
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

cd "{remote_pkg_dir}"

echo "=== D. ABAQUS DATACHECK ==="
abaqus job=M2STATE_FRACFIX_RESTART1R1R9_DATACHECK user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R9.inp datacheck interactive

echo "=== E. STEP 1 QUALIFICATION SOLVE ==="
# Generate a Step-1 only deck by cutting at Step 2
python3 -c "
from pathlib import Path
p = Path('M2STATE_FRACFIX_RESTART1R1R9.inp')
lines = p.read_text().splitlines()
step1_lines = []
for l in lines:
    if '*STEP, NAME=Step-2-Continuation' in l:
        break
    step1_lines.append(l)

while step1_lines and (step1_lines[-1].startswith('**') or not step1_lines[-1].strip()):
    step1_lines.pop()

Path('M2STATE_FRACFIX_RESTART1R1R9_STEP1.inp').write_text('\\n'.join(step1_lines) + '\\n')
"

abaqus job=M2STATE_FRACFIX_RESTART1R1R9_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R9_STEP1.inp interactive

echo "=== F. CHECKING STEP 1 REACTION FORCES & SDV OUTPUT ==="
python3 -c "
import re
with open('M2STATE_FRACFIX_RESTART1R1R9_STEP1.dat') as f:
    text = f.read()

# Extract node 99999 reaction force
lines = text.splitlines()
rp_rf1 = None
for l in lines:
    parts = l.split()
    if len(parts) >= 3 and parts[0] == '99999':
        try:
            rp_rf1 = float(parts[1])
            print('Step 1 RP Node 99999 RF1 =', rp_rf1, 'kN')
        except:
            pass

# Check bottom nodes sum
bot_rf1_sum = 0.0
in_rf_table = False
for l in lines:
    if 'RF1' in l and 'RF2' in l:
        in_rf_table = True
        continue
    if in_rf_table:
        parts = l.split()
        if len(parts) >= 3:
            try:
                nid = int(parts[0])
                if nid != 99999:
                    bot_rf1_sum += float(parts[1])
            except:
                pass
        if 'TOTAL' in l:
            in_rf_table = False

print('Bottom nodes RF1 sum =', bot_rf1_sum, 'kN')
if rp_rf1 is not None:
    balance_err = abs(rp_rf1 + bot_rf1_sum)
    print('Global force balance error = %.6e kN' % balance_err)
    
    # Predecessor comparison: 1386469.mmaster02 RF1 = 0.064100 kN
    rf_pred = 0.064100
    rel_diff = abs(rp_rf1 - rf_pred) / rf_pred
    print('Relative difference to MM source (0.064100 kN): %.6f (%.3f%%)' % (rel_diff, rel_diff * 100))
    if rel_diff <= 0.02:
        print('FORCE CONTINUITY GATE: PASS')
    else:
        print('FORCE CONTINUITY GATE: FAIL')

# Check SDV output in DAT
sdv_count = text.count('SDV')
print('Occurrences of SDV in Step 1 DAT:', sdv_count)
"

echo "=== G. GUARDED WRAPPER DRY-RUN ==="
./submit_m2state_fracfix_restart1r1r9.sh --dry-run

echo "=== QUALIFICATION COMPLETED SUCCESSFULLY ==="
"""

    ssh_run = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, f'bash -s']
    proc = subprocess.Popen(ssh_run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = proc.communicate(input=remote_script)
    print(out)
    if proc.returncode != 0:
        print(f"ERROR: Qualification failed with returncode {proc.returncode}")
        sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
