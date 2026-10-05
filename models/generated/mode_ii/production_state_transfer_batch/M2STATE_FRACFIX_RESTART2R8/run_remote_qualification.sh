#!/bin/bash
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8
chmod +x submit_m2state_fracfix_restart2r8.sh job_notifications.sh

echo '=== Step 1: Remote SHA256 Manifest Verification ==='
python3 -c "
import json, hashlib, sys
with open('PACKAGE_MANIFEST.json') as f: m = json.load(f)
for fn, expected in m['file_hashes'].items():
    h = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    if h != expected:
        print(f'MISMATCH: {fn} actual={h} expected={expected}')
        sys.exit(1)
print('Remote package integrity verified: 100% SHA256 match.')
"

echo '=== Step 2: Abaqus 2023 Datacheck ==='
rm -f M2STATE_FRACFIX_RESTART2R8.lck *.log *.dat *.msg *.sta *.prt *.com *.sim *.odb || true
abaqus job=M2STATE_FRACFIX_RESTART2R8 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R8.inp datacheck interactive
if grep -q 'ANALYSIS DATACHECK COMPLETE' M2STATE_FRACFIX_RESTART2R8.dat || grep -q 'THE ANALYSIS HAS BEEN COMPLETED' M2STATE_FRACFIX_RESTART2R8.dat; then
    echo 'DATACHECK SUCCESS: Analysis completed without errors.'
else
    echo 'DATACHECK FAILED!'
    cat M2STATE_FRACFIX_RESTART2R8.dat | tail -n 40
    exit 1
fi

echo '=== Step 3: Interactive Step-1 Qualification Solve ==='
python3 -c "
lines = open('M2STATE_FRACFIX_RESTART2R8.inp').readlines()
s1_lines = []
for l in lines:
    s1_lines.append(l)
    if '*END STEP' in l:
        break
open('M2STATE_FRACFIX_RESTART2R8_STEP1.inp', 'w').writelines(s1_lines)
"
rm -f M2STATE_FRACFIX_RESTART2R8_STEP1.lck *.log *.dat *.msg *.sta *.prt *.com *.sim *.odb || true
abaqus job=M2STATE_FRACFIX_RESTART2R8_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R8_STEP1.inp interactive double=both cpus=1 memory='4000 mb'
if grep -q 'THE ANALYSIS HAS BEEN COMPLETED' M2STATE_FRACFIX_RESTART2R8_STEP1.dat; then
    echo 'STEP 1 SOLVE SUCCESS: Converged without errors.'
else
    echo 'STEP 1 SOLVE FAILED!'
    cat M2STATE_FRACFIX_RESTART2R8_STEP1.dat | tail -n 40
    exit 1
fi

echo '=== Step 4: Extract Step 1 Reaction Force and Displacements ==='
python3 -c "
import json
text = open('M2STATE_FRACFIX_RESTART2R8_STEP1.dat').read()
bottom_rf1 = 0.0
for line in text.splitlines():
    parts = line.split()
    if len(parts) >= 5 and parts[0].isdigit():
        nid = int(parts[0])
        if 1 <= nid <= 120:
            try:
                if len(parts) == 8:
                    rf1 = float(parts[5])
                elif len(parts) == 7:
                    rf1 = float(parts[4])
                else:
                    rf1 = float(parts[-3])
                bottom_rf1 += rf1
            except: pass
print(f'STEP 1 QUALIFICATION: Bottom RF1 Sum = {-bottom_rf1:.6f} kN')
with open('STEP1_QUALIFICATION_RESULTS.json', 'w') as out_f:
    json.dump({'step1_bottom_rf1_kN': -bottom_rf1}, out_f, indent=2)
"

echo '=== Step 5: Guarded Wrapper Dry-Run Verification ==='
./submit_m2state_fracfix_restart2r8.sh --dry-run
