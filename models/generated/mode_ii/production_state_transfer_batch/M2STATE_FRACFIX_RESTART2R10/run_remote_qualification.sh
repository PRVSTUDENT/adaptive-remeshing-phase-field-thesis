#!/bin/bash
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp}
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R10
chmod +x submit_m2state_fracfix_restart2r10.sh job_notifications.sh validate_package_manifest.py

echo "=== Step 1: Remote SHA256 Manifest Verification ==="
python3 validate_package_manifest.py

echo "=== Step 2: Abaqus 2023 Datacheck ==="
rm -f M2STATE_FRACFIX_RESTART2R10.lck M2STATE_FRACFIX_RESTART2R10.dat M2STATE_FRACFIX_RESTART2R10.msg M2STATE_FRACFIX_RESTART2R10.sta M2STATE_FRACFIX_RESTART2R10.prt M2STATE_FRACFIX_RESTART2R10.com M2STATE_FRACFIX_RESTART2R10.sim M2STATE_FRACFIX_RESTART2R10.odb || true
abaqus job=M2STATE_FRACFIX_RESTART2R10 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R10.inp datacheck interactive
if grep -q "ANALYSIS DATACHECK COMPLETE" M2STATE_FRACFIX_RESTART2R10.dat || grep -q "THE ANALYSIS HAS BEEN COMPLETED" M2STATE_FRACFIX_RESTART2R10.dat; then
    echo "DATACHECK SUCCESS: Analysis completed without errors."
else
    echo "DATACHECK FAILED!"
    cat M2STATE_FRACFIX_RESTART2R10.dat | tail -n 40
    exit 1
fi

echo "=== Step 3: Interactive Step-1 Qualification Solve ==="
python3 -c "
lines = open('M2STATE_FRACFIX_RESTART2R10.inp').readlines()
s1_lines = []
for l in lines:
    s1_lines.append(l)
    if '*END STEP' in l:
        break
open('M2STATE_FRACFIX_RESTART2R10_STEP1.inp', 'w').writelines(s1_lines)
"
rm -f M2STATE_FRACFIX_RESTART2R10_STEP1.lck M2STATE_FRACFIX_RESTART2R10_STEP1.dat M2STATE_FRACFIX_RESTART2R10_STEP1.msg M2STATE_FRACFIX_RESTART2R10_STEP1.sta M2STATE_FRACFIX_RESTART2R10_STEP1.prt M2STATE_FRACFIX_RESTART2R10_STEP1.com M2STATE_FRACFIX_RESTART2R10_STEP1.sim M2STATE_FRACFIX_RESTART2R10_STEP1.odb M2STATE_FRACFIX_RESTART2R10_STEP1.mdl M2STATE_FRACFIX_RESTART2R10_STEP1.stt || true
abaqus job=M2STATE_FRACFIX_RESTART2R10_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R10_STEP1.inp interactive double=both cpus=1 memory="4000 mb"
if grep -q "THE ANALYSIS HAS BEEN COMPLETED" M2STATE_FRACFIX_RESTART2R10_STEP1.dat; then
    echo "STEP 1 SOLVE SUCCESS: Converged without errors."
else
    echo "STEP 1 SOLVE FAILED!"
    cat M2STATE_FRACFIX_RESTART2R10_STEP1.dat | tail -n 40
    exit 1
fi

echo "=== Step 4: Extract Step 1 Reaction Force and Global Balance ==="
cat << 'PYEOF' > extract_rf.py
from odbAccess import openOdb
import json, sys

try:
    odb = openOdb('M2STATE_FRACFIX_RESTART2R10_STEP1.odb')
    step = odb.steps[odb.steps.keys()[0]]
    frame = step.frames[-1]
    rf_field = frame.fieldOutputs['RF']
    
    rp_rf1 = 0.0
    bot_rf1 = 0.0
    
    for v in rf_field.values:
        if v.nodeLabel == 99999:
            rp_rf1 = float(v.data[0])
        elif 1 <= v.nodeLabel <= 201:
            bot_rf1 += float(v.data[0])
            
    odb.close()
except Exception as e:
    print("ODB extract error:", str(e))
    # Fallback to DAT file parsing
    text = open('M2STATE_FRACFIX_RESTART2R10_STEP1.dat').read()
    rp_rf1 = 0.0
    bot_rf1 = 0.0
    for line in text.splitlines():
        if '99999' in line:
            parts = line.strip().split()
            if len(parts) >= 2:
                try: rp_rf1 = float(parts[-1])
                except: pass

predecessor_rf1 = 0.123223
balance_err = abs(rp_rf1 + bot_rf1)
force_diff_abs = abs(rp_rf1 - predecessor_rf1)
force_diff_rel = force_diff_abs / predecessor_rf1
force_pass = force_diff_rel <= 0.02

print("STEP 1 QUALIFICATION: RP 99999 RF1 = %.6f kN" % rp_rf1)
print("STEP 1 QUALIFICATION: Bottom RF1 Sum = %.6f kN" % bot_rf1)
print("STEP 1 QUALIFICATION: Global Force Balance Error = %.6e kN" % balance_err)
print("FORCE CONTINUITY: Predecessor (1389241) = %.6f kN, R2R10 Step 1 = %.6f kN" % (predecessor_rf1, rp_rf1))
print("FORCE CONTINUITY: Abs Diff = %.6f kN, Rel Diff = %.6f (%.3f%%)" % (force_diff_abs, force_diff_rel, force_diff_rel*100.0))
print("FORCE CONTINUITY GATE PASS = %s" % str(force_pass))

res = {
    "step1_rp_rf1_kN": rp_rf1,
    "step1_bottom_rf1_sum_kN": bot_rf1,
    "global_force_balance_error_kN": balance_err,
    "predecessor_job_1389241_rf1_kN": predecessor_rf1,
    "force_continuity_abs_diff_kN": force_diff_abs,
    "force_continuity_rel_diff": force_diff_rel,
    "force_continuity_gate_pass": force_pass,
    "global_force_balance_pass": balance_err <= 1.0e-5,
    "step1_solve_pass": True
}

with open('STEP1_QUALIFICATION_RESULTS.json', 'w') as out_f:
    json.dump(res, out_f, indent=2)
PYEOF

abaqus python extract_rf.py

echo "=== Step 5: Guarded Wrapper Dry-Run Verification ==="
./submit_m2state_fracfix_restart2r10.sh --dry-run
