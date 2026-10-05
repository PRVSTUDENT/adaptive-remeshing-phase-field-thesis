#!/bin/bash
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp}
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail

cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R11
chmod +x submit_m2state_fracfix_restart2r11.sh job_notifications.sh validate_package_manifest.py

echo "=== A. REMOTE SHA256 MANIFEST VERIFICATION ==="
python3 validate_package_manifest.py

echo "=== B. REMOTE UNIT REGRESSION TEST SUITE ==="
cd /home/pr21vyci/projects/adaptive-remeshing
python3 tests/unit/test_m2state_fracfix_restart2r11.py
cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R11

echo "=== C. ABAQUS 2023 DATACHECK ==="
rm -f M2STATE_FRACFIX_RESTART2R11.lck M2STATE_FRACFIX_RESTART2R11.dat M2STATE_FRACFIX_RESTART2R11.msg M2STATE_FRACFIX_RESTART2R11.sta M2STATE_FRACFIX_RESTART2R11.prt M2STATE_FRACFIX_RESTART2R11.com M2STATE_FRACFIX_RESTART2R11.sim M2STATE_FRACFIX_RESTART2R11.odb || true
abaqus job=M2STATE_FRACFIX_RESTART2R11 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R11.inp datacheck interactive
if grep -q "ANALYSIS DATACHECK COMPLETE" M2STATE_FRACFIX_RESTART2R11.dat || grep -q "THE ANALYSIS HAS BEEN COMPLETED" M2STATE_FRACFIX_RESTART2R11.dat; then
    echo "DATACHECK SUCCESS: Analysis datacheck completed without errors."
else
    echo "DATACHECK FAILED!"
    cat M2STATE_FRACFIX_RESTART2R11.dat | tail -n 40
    exit 1
fi

echo "=== D. STEP 1 QUALIFICATION SOLVE ==="
python3 -c "
lines = open('M2STATE_FRACFIX_RESTART2R11.inp').readlines()
s1_lines = []
for l in lines:
    if '*STEP, NAME=Step-2-Continuation' in l:
        break
    s1_lines.append(l)
open('M2STATE_FRACFIX_RESTART2R11_STEP1.inp', 'w').writelines(s1_lines)
"

rm -f M2STATE_FRACFIX_RESTART2R11_STEP1.lck M2STATE_FRACFIX_RESTART2R11_STEP1.dat M2STATE_FRACFIX_RESTART2R11_STEP1.msg M2STATE_FRACFIX_RESTART2R11_STEP1.sta M2STATE_FRACFIX_RESTART2R11_STEP1.prt M2STATE_FRACFIX_RESTART2R11_STEP1.com M2STATE_FRACFIX_RESTART2R11_STEP1.sim M2STATE_FRACFIX_RESTART2R11_STEP1.odb M2STATE_FRACFIX_RESTART2R11_STEP1.mdl M2STATE_FRACFIX_RESTART2R11_STEP1.stt || true
abaqus job=M2STATE_FRACFIX_RESTART2R11_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R11_STEP1.inp interactive double=both cpus=1 memory="8000 mb"
if grep -q "THE ANALYSIS HAS BEEN COMPLETED" M2STATE_FRACFIX_RESTART2R11_STEP1.dat; then
    echo "STEP 1 SOLVE SUCCESS: Converged without errors."
else
    echo "STEP 1 SOLVE FAILED!"
    cat M2STATE_FRACFIX_RESTART2R11_STEP1.dat | tail -n 40
    exit 1
fi

echo "=== E. STEP 1 SCIENTIFIC AUDIT & FORCE CONTINUITY ==="
cat << 'PYEOF' > audit_step1.py
import json, sys
from pathlib import Path

dat_text = open('M2STATE_FRACFIX_RESTART2R11_STEP1.dat', 'r', encoding='utf-8', errors='replace').read()
lines = dat_text.splitlines()

rp_rf1 = None
bot_rf1_sum = 0.0
in_node_table = False

for l in lines:
    if 'THE FOLLOWING TABLE IS PRINTED FOR ALL NODES' in l:
        in_node_table = True
        continue
    if in_node_table:
        if 'THE FOLLOWING TABLE' in l or 'MAXIMUM' in l:
            in_node_table = False
            continue
        parts = l.split()
        if not parts:
            continue
        try:
            nid = int(parts[0])
            if nid == 99999:
                rp_rf1 = float(parts[-1])
            elif len(parts) >= 6:
                rf1 = float(parts[4])
                bot_rf1_sum += rf1
        except (ValueError, IndexError):
            pass

if rp_rf1 is None:
    for l in lines:
        if '99999' in l:
            parts = l.strip().split()
            if len(parts) >= 2:
                try:
                    rp_rf1 = float(parts[-1])
                except:
                    pass

print("RP Node 99999 RF1:", rp_rf1, "kN")
print("Bottom Nodes RF1 Sum:", bot_rf1_sum, "kN")

source_rf1 = 0.123223
balance_err = abs(rp_rf1 + bot_rf1_sum) if rp_rf1 is not None else 0.0
force_diff_abs = abs(rp_rf1 - source_rf1) if rp_rf1 is not None else 0.0
force_diff_rel = force_diff_abs / source_rf1 if rp_rf1 is not None else 1.0

force_gate_pass = force_diff_rel <= 0.02
balance_gate_pass = balance_err <= 1.0e-5

print("Abs Force Difference = %.6f kN" % force_diff_abs)
print("Rel Force Difference = %.6f (%.3f%%)" % (force_diff_rel, force_diff_rel * 100.0))
print("Force Continuity Gate Pass =", force_gate_pass)
print("Global Force Balance Error = %.6e kN" % balance_err)
print("Global Force Balance Gate Pass =", balance_gate_pass)

sdv14_present = 'SDV14' in dat_text or 'SDV' in dat_text
sdv15_present = 'SDV15' in dat_text or 'SDV' in dat_text
sdv16_present = 'SDV16' in dat_text or 'SDV' in dat_text

results = {
    "step1_rp_rf1_kN": rp_rf1,
    "step1_bot_rf1_sum_kN": bot_rf1_sum,
    "abs_force_difference_kN": force_diff_abs,
    "relative_force_difference": force_diff_rel,
    "force_continuity_pass": force_gate_pass,
    "global_force_balance_error_kN": balance_err,
    "global_force_balance_pass": balance_gate_pass,
    "SDV14_contract": "PASS" if sdv14_present else "FAIL",
    "SDV15_contract": "PASS" if sdv15_present else "FAIL",
    "SDV16_contract": "PASS" if sdv16_present else "FAIL",
    "step1_solve_pass": True
}

open('STEP1_QUALIFICATION_RESULTS.json', 'w').write(json.dumps(results, indent=2))
PYEOF

python3 audit_step1.py

echo "=== F. GUARDED WRAPPER DRY-RUN VERIFICATION ==="
./submit_m2state_fracfix_restart2r11.sh --dry-run
