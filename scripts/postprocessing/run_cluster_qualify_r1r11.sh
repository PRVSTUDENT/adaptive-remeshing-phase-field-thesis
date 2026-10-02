#!/bin/bash
set -e

export XDG_RUNTIME_DIR=/tmp/pr21vyci-runtime
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

CANDIDATE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11"
REPO_DIR="/home/pr21vyci/projects/adaptive-remeshing"

echo "=== A. MANIFEST PREFLIGHT ==="
cd "$CANDIDATE_DIR"
python3 validate_package_manifest.py

echo "=== B. RUNNING UNIT & REGRESSION TESTS ==="
cd "$REPO_DIR"
python3 tests/unit/test_m2state_fracfix_restart1r1r11.py

echo "=== C. LOADING MODULES ==="
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

cd "$CANDIDATE_DIR"

echo "=== D. ABAQUS DATACHECK ==="
abaqus job=M2STATE_FRACFIX_RESTART1R1R11_DATACHECK user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R11.inp datacheck interactive

echo "=== E. STEP 1 QUALIFICATION SOLVE ==="
python3 -c "
from pathlib import Path
p = Path('M2STATE_FRACFIX_RESTART1R1R11.inp')
lines = p.read_text().splitlines()
step1_lines = []
for l in lines:
    if '*STEP, NAME=Step-2-Continuation' in l:
        break
    step1_lines.append(l)

while step1_lines and (step1_lines[-1].startswith('**') or not step1_lines[-1].strip()):
    step1_lines.pop()

Path('M2STATE_FRACFIX_RESTART1R1R11_STEP1.inp').write_text('\n'.join(step1_lines) + '\n')
"

abaqus job=M2STATE_FRACFIX_RESTART1R1R11_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R11_STEP1.inp interactive

echo "=== F. CHECKING STEP 1 REACTION FORCES & SDV OUTPUT ==="
python3 -c "
import sys
from pathlib import Path

dat_path = Path('M2STATE_FRACFIX_RESTART1R1R11_STEP1.dat')
text = dat_path.read_text(encoding='utf-8', errors='replace')
lines = text.splitlines()

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

print('RP Node 99999 RF1:', rp_rf1, 'kN')
print('Bottom nodes RF1 sum:', bot_rf1_sum, 'kN')
balance_err = abs(rp_rf1 + bot_rf1_sum)
print('Global force balance error = %.6e kN' % balance_err)

rf_pred = 0.064100
rel_diff = abs(rp_rf1 - rf_pred) / rf_pred
print('Relative difference to MM source (0.064100 kN): %.6f (%.3f%%)' % (rel_diff, rel_diff * 100))
if rel_diff <= 0.02:
    print('FORCE CONTINUITY GATE: PASS')
else:
    print('FORCE CONTINUITY GATE: FAIL')
    sys.exit(1)

sdv_count = text.count('SDV16')
print('Occurrences of SDV16 in Step 1 DAT:', sdv_count)
if sdv_count > 0:
    print('SDV16 OUTPUT GATE: PASS')
else:
    print('SDV16 OUTPUT GATE: FAIL')
    sys.exit(1)
"

echo "=== G. GUARDED WRAPPER DRY-RUN ==="
./submit_m2state_fracfix_restart1r1r11.sh --dry-run

echo "=== QUALIFICATION COMPLETED SUCCESSFULLY ==="
