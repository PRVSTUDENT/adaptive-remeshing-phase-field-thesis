#!/bin/bash
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp}
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R9
chmod +x submit_m2state_fracfix_restart2r9.sh job_notifications.sh validate_package_manifest.py

echo '=== Step 1: Remote SHA256 Manifest Verification ==='
python3 validate_package_manifest.py

echo '=== Step 2: Abaqus 2023 Datacheck ==='
rm -f M2STATE_FRACFIX_RESTART2R9.lck *.log *.dat *.msg *.sta *.prt *.com *.sim *.odb || true
abaqus job=M2STATE_FRACFIX_RESTART2R9 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R9.inp datacheck interactive
if grep -q 'ANALYSIS DATACHECK COMPLETE' M2STATE_FRACFIX_RESTART2R9.dat || grep -q 'THE ANALYSIS HAS BEEN COMPLETED' M2STATE_FRACFIX_RESTART2R9.dat; then
    echo 'DATACHECK SUCCESS: Analysis completed without errors.'
else
    echo 'DATACHECK FAILED!'
    cat M2STATE_FRACFIX_RESTART2R9.dat | tail -n 40
    exit 1
fi

echo '=== Step 3: Interactive Step-1 Qualification Solve ==='
python3 -c "
lines = open('M2STATE_FRACFIX_RESTART2R9.inp').readlines()
s1_lines = []
for l in lines:
    s1_lines.append(l)
    if '*END STEP' in l:
        break
open('M2STATE_FRACFIX_RESTART2R9_STEP1.inp', 'w').writelines(s1_lines)
"
rm -f M2STATE_FRACFIX_RESTART2R9_STEP1.lck *.log *.dat *.msg *.sta *.prt *.com *.sim *.odb || true
abaqus job=M2STATE_FRACFIX_RESTART2R9_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R9_STEP1.inp interactive double=both cpus=1 memory='4000 mb'
if grep -q 'THE ANALYSIS HAS BEEN COMPLETED' M2STATE_FRACFIX_RESTART2R9_STEP1.dat; then
    echo 'STEP 1 SOLVE SUCCESS: Converged without errors.'
else
    echo 'STEP 1 SOLVE FAILED!'
    cat M2STATE_FRACFIX_RESTART2R9_STEP1.dat | tail -n 40
    exit 1
fi

echo '=== Step 4: Extract Step 1 Reaction Force and Global Balance ==='
python3 -c "
import json
text = open('M2STATE_FRACFIX_RESTART2R9_STEP1.dat').read()
rp_rf1 = 0.0
bottom_rf1 = 0.0
for line in text.splitlines():
    sline = line.strip()
    if sline.startswith('99999'):
        parts = sline.split()
        if len(parts) >= 2:
            rp_rf1 = float(parts[-1])
    elif len(sline) > 0 and sline[0].isdigit():
        parts = sline.split()
        if len(parts) >= 4:
            try:
                nid = int(parts[0])
                if 1 <= nid <= 121:
                    rf1 = float(parts[-3]) if len(parts) >= 8 else (float(parts[-2]) if len(parts) >= 7 else float(parts[-1]))
                    bottom_rf1 += rf1
            except: pass
balance_err = abs(rp_rf1 + bottom_rf1)
predecessor_rf1 = 0.123223
force_diff_abs = abs(rp_rf1 - predecessor_rf1)
force_diff_rel = force_diff_abs / predecessor_rf1
print(f'STEP 1 QUALIFICATION: RP 99999 RF1 = {rp_rf1:.6f} kN')
print(f'STEP 1 QUALIFICATION: Bottom RF1 Sum = {bottom_rf1:.6f} kN')
print(f'STEP 1 QUALIFICATION: Global Force Balance Error = {balance_err:.6e} kN')
print(f'FORCE CONTINUITY: Predecessor (1389241) = {predecessor_rf1:.6f} kN, R2R9 Step 1 = {rp_rf1:.6f} kN')
print(f'FORCE CONTINUITY: Abs Diff = {force_diff_abs:.6f} kN, Rel Diff = {force_diff_rel:.6f} ({force_diff_rel*100.0:.3f}%)')
res = {
    'step1_rp_rf1_kN': rp_rf1,
    'step1_bottom_rf1_sum_kN': bottom_rf1,
    'global_force_balance_error_kN': balance_err,
    'predecessor_job_1389241_rf1_kN': predecessor_rf1,
    'force_continuity_abs_diff_kN': force_diff_abs,
    'force_continuity_rel_diff': force_diff_rel,
    'global_force_balance_pass': balance_err <= 1.0e-5,
    'step1_solve_pass': True
}
with open('STEP1_QUALIFICATION_RESULTS.json', 'w') as out_f:
    json.dump(res, out_f, indent=2)
"

echo '=== Step 5: Guarded Wrapper Dry-Run Verification ==='
./submit_m2state_fracfix_restart2r9.sh --dry-run
