#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

module load abaqus/2023 gcc/11.4.0 intel/2024.2.0

echo "=== STEP 1: EXTRACTING RAW MISESERI FIELD FROM Job-1_UEL.odb ==="
abaqus python extract_mode2_miseseri_field.py Job-1_UEL.odb .

echo "=== STEP 2: EXECUTING NATIVE REMESHING SWEEP (ET in 1, 2, 3, 5%) ==="
abaqus cae noGUI=execute_mode2_native_remesh_suite.py -- Job-1_UEL.odb .

echo "=== STEP 3: BUILDING PRODUCTION Job-2_UEL.inp FOR QUALIFIED CANDIDATE ==="
python3 -c "
import json, os, sys

with open('MODE2_NATIVE_REMESH_SWEEP_SUMMARY.json') as f:
    data = json.load(f)

# Hierarchy: consistent path -> resolution of l0=0.015 mm -> no spurious branches -> mesh quality
candidates = []
for k, v in data.items():
    et = float(v.get('error_target_pct', 0))
    cls = v.get('classification', '')
    angle = v.get('corridor_chord_angle_deg', 0)
    end_x = v.get('corridor_end_x_at_y0', 0)
    spurious = v.get('has_spurious_branches', True)
    elems = v.get('total_elements', 0)
    h_min = v.get('min_element_size_mm', 1.0)
    
    score = 0
    if cls == 'MODE2_LOCALIZATION_CONSISTENT_WITH_PUBLISHED_PATH':
        score += 100
    elif cls == 'MODE2_LOCALIZATION_ACCEPTABLE_MARGINAL_DEVIATION':
        score += 50
    if not spurious:
        score += 30
    if h_min <= 0.0075: # <= l0/2
        score += 20
    # Prefer moderate mesh size near ~20k (published 19,963)
    size_penalty = abs(elems - 19963) / 1000.0
    score -= size_penalty
    candidates.append((score, et, elems, cls, k))

candidates.sort(key=lambda x: x[0], reverse=True)
best = candidates[0]
best_et = int(best[1])
print('Ranked candidates:')
for c in candidates:
    print('  ET %d%%: score=%.2f, elements=%d, classification=%s' % (int(c[1]), c[0], c[2], c[3]))
print('--> Selected best candidate: errorTarget = %d%% (elements = %d)' % (best_et, best[2]))

raw_inp = 'MODE2_ADAPTED_RAW_%dPCT.inp' % best_et
ret = os.system('python3 build_mode2_adapted_job2_deck.py %s Job-2_UEL.inp Job-2_UEL' % raw_inp)
if ret != 0:
    print('ERROR: deck building failed with code', ret)
    sys.exit(1)
"

echo "=== STEP 4: RUNNING DIRECT ABAQUS DATACHECK ON Job-2_UEL.inp ==="
rm -f Job-2_UEL_DATACHECK.* || true
abaqus datacheck job=Job-2_UEL_DATACHECK input=Job-2_UEL.inp user=f42_mixed_uel.for interactive memory="8000mb" cpus=1
DC_EXIT=$?
echo "=== DATACHECK EXIT CODE: $DC_EXIT ==="

if [ "$DC_EXIT" -eq 0 ]; then
    echo "=== DATACHECK PASSED CLEANLY (EXIT 0) ==="
else
    echo "=== ERROR: DATACHECK FAILED (EXIT $DC_EXIT) ==="
    cat Job-2_UEL_DATACHECK.msg 2>/dev/null || true
    cat Job-2_UEL_DATACHECK.dat 2>/dev/null || true
    exit "$DC_EXIT"
fi

echo "=== STAGE 15C PIPELINE COMPLETED SUCCESSFULLY ==="
