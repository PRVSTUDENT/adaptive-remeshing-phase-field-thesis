#!/usr/bin/env python3
"""
Remote Qualification Script for Candidate M2STATE_FRACFIX_RESTART1R1R8.
Task ID: F84STATE-M2-CORRECTED-RESTART1-JACOBIAN-INVERSE-REPAIR-QUALIFICATION1
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8"

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8'

    print("=== 1. SYNCING PACKAGE TO CLUSTER ===")
    ssh_mkdir = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, f'mkdir -p {remote_pkg_dir}']
    subprocess.run(ssh_mkdir, check=True)

    files_to_sync = [
        "M2STATE_FRACFIX_RESTART1R1R8.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R8.pbs",
        "submit_m2state_fracfix_restart1r1r8.sh",
        "PACKAGE_MANIFEST.json"
    ]

    for fn in files_to_sync:
        local_p = LOCAL_PKG_DIR / fn
        scp_cmd = ['scp', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', str(local_p), f'{host}:{remote_pkg_dir}/{fn}']
        subprocess.run(scp_cmd, check=True)

    print("=== 2. RUNNING REMOTE VALIDATION, DATACHECK, AND STEP-1 SOLVE ===")
    remote_script = f"""#!/bin/bash
set -e
export XDG_RUNTIME_DIR=/tmp/pr21vyci-runtime
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

cd "{remote_pkg_dir}"

echo "=== A. MANIFEST PREFLIGHT ==="
python3 validate_package_manifest.py PACKAGE_MANIFEST.json

echo "=== B. LOADING MODULES ==="
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "=== C. ABAQUS DATACHECK ==="
abaqus job=M2STATE_FRACFIX_RESTART1R1R8_DATACHECK user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R8.inp datacheck interactive

echo "=== D. STEP 1 QUALIFICATION SOLVE ==="
# Generate a Step-1 only deck by cutting at Step 2
python3 -c "
from pathlib import Path
p = Path('M2STATE_FRACFIX_RESTART1R1R8.inp')
lines = p.read_text().splitlines()
step1_lines = []
for l in lines:
    if '*STEP, NAME=Step-2-Continuation' in l:
        break
    step1_lines.append(l)

while step1_lines and (step1_lines[-1].startswith('**') or not step1_lines[-1].strip()):
    step1_lines.pop()

Path('M2STATE_FRACFIX_RESTART1R1R8_STEP1.inp').write_text('\\n'.join(step1_lines) + '\\n')
"

abaqus job=M2STATE_FRACFIX_RESTART1R1R8_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R8_STEP1.inp interactive



echo "=== E. PARSING STEP 1 REACTION FORCES ==="
python3 -c "
with open('M2STATE_FRACFIX_RESTART1R1R8_STEP1.dat') as f:
    dat = f.read()

# Extract node 99999 line
rp_u1 = None
rp_rf1 = None
for l in dat.splitlines():
    parts = l.strip().split()
    if len(parts) >= 3 and parts[0] == '99999':
        rp_u1 = float(parts[1])
        rp_rf1 = float(parts[2]) if len(parts) == 3 else float(parts[-1])
        print(f'[EXTRACTED] RP Node 99999: U1={{rp_u1:.6e}}, RF1={{rp_rf1:.6f}}')
        break

# Extract bottom boundary sum
# Parse bottom node set
with open('M2STATE_FRACFIX_RESTART1R1R8.inp') as f:
    inp_lines = f.readlines()

bottom_nodes = []
in_b = False
for l in inp_lines:
    if 'NSET=N_BOTTOM' in l:
        in_b = True
        continue
    if in_b:
        if l.startswith('*'):
            in_b = False
            continue
        parts = [int(p.strip()) for p in l.split(',') if p.strip().isdigit()]
        bottom_nodes.extend(parts)

# Parse table
bottom_rf1_sum = 0.0
in_tab = False
for l in dat.splitlines():
    if 'THE FOLLOWING TABLE IS PRINTED FOR ALL NODES' in l:
        in_tab = True
        continue
    if in_tab:
        parts = l.strip().split()
        if len(parts) >= 6 and parts[0].isdigit():
            node = int(parts[0])
            if node in bottom_nodes:
                bottom_rf1_sum += float(parts[4])
        elif 'MAXIMUM' in l:
            in_tab = False

print(f'[EXTRACTED] Sum Bottom RF1 on {{len(bottom_nodes)}} nodes: {{bottom_rf1_sum:.6f}}')
balance_err = abs(rp_rf1 + bottom_rf1_sum) if (rp_rf1 is not None) else None
print(f'[EXTRACTED] Global force balance error: {{balance_err:.6e}}')

# Predecessor comparison
valid_MM_RF1 = 0.064100
abs_diff = abs(rp_rf1 - valid_MM_RF1)
rel_diff = abs_diff / valid_MM_RF1
print(f'[EXTRACTED] valid_MM_source_RF1_kN = {{valid_MM_RF1:.6f}}')
print(f'[EXTRACTED] corrected_Restart1_Step1_RF1_kN = {{rp_rf1:.6f}}')
print(f'[EXTRACTED] force_absolute_difference_kN = {{abs_diff:.6f}}')
print(f'[EXTRACTED] force_relative_difference = {{rel_diff:.6f}}')
print(f'[EXTRACTED] force_continuity_gate (< 0.02) = {{rel_diff < 0.02}}')
"
"""
    clean_bytes = remote_script.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'bash -s']
    res = subprocess.run(cmd, input=clean_bytes, capture_output=True)
    print("STDOUT:\n", res.stdout.decode('utf-8', errors='replace'))
    print("STDERR:\n", res.stderr.decode('utf-8', errors='replace'))

if __name__ == "__main__":
    main()


