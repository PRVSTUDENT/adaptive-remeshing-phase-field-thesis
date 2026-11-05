#!/bin/bash
set -euo pipefail
RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

echo "=== Running Preliminary Mechanical Subproblem Datacheck (P172) ==="
abaqus job=P172_MECHANICAL_DC user=f42_mixed_uel.for input=P172_MECHANICAL_DC.inp cpus=1 memory="8 gb" datacheck interactive > P172_MECHANICAL_DC.stdout.txt 2>&1
test -f "P172_MECHANICAL_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P172_MECHANICAL_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P172_MECHANICAL_DC.dat"
if grep -q '\*\*\*ERROR' "P172_MECHANICAL_DC.dat"; then echo "MECHANICAL DATACHECK ERROR"; exit 66; fi
echo "P172_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Preliminary Phase Subproblem Datacheck (P172) ==="
abaqus job=P172_PHASE_DC user=f42_mixed_uel.for input=P172_PHASE_DC.inp cpus=1 memory="8 gb" datacheck interactive > P172_PHASE_DC.stdout.txt 2>&1
test -f "P172_PHASE_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P172_PHASE_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P172_PHASE_DC.dat"
if grep -q '\*\*\*ERROR' "P172_PHASE_DC.dat"; then echo "PHASE DATACHECK ERROR"; exit 67; fi
echo "P172_PHASE_DC: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Dynamic First-Iteration Mechanical Subproblem Datacheck (P172) ==="
abaqus job=P172_ITER1_MECH user=f42_mixed_uel.for input=P172_ITER1_MECH.inp cpus=1 memory="8 gb" datacheck interactive > P172_ITER1_MECH.stdout.txt 2>&1
test -f "P172_ITER1_MECH.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P172_ITER1_MECH.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P172_ITER1_MECH.dat"
if grep -q '\*\*\*ERROR' "P172_ITER1_MECH.dat"; then echo "DYNAMIC ITER1 MECHANICAL DATACHECK ERROR"; exit 68; fi
echo "P172_ITER1_MECH: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Dynamic First-Iteration Phase Subproblem Datacheck (P172) ==="
abaqus job=P172_ITER1_PHASE user=f42_mixed_uel.for input=P172_ITER1_PHASE.inp cpus=1 memory="8 gb" datacheck interactive > P172_ITER1_PHASE.stdout.txt 2>&1
test -f "P172_ITER1_PHASE.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P172_ITER1_PHASE.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P172_ITER1_PHASE.dat"
if grep -q '\*\*\*ERROR' "P172_ITER1_PHASE.dat"; then echo "DYNAMIC ITER1 PHASE DATACHECK ERROR"; exit 69; fi
echo "P172_ITER1_PHASE: AUTHENTIC_DATACHECK_PASS"
