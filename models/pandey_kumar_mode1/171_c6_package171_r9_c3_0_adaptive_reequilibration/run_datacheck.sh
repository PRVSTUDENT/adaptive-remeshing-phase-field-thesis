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

echo "=== Running Mechanical Subproblem Datacheck ==="
abaqus job=P171_MECHANICAL_DC user=f42_mixed_uel.for input=P171_MECHANICAL_DC.inp cpus=1 memory="8 gb" datacheck interactive > P171_MECHANICAL_DC.stdout.txt 2>&1
test -f "P171_MECHANICAL_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P171_MECHANICAL_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P171_MECHANICAL_DC.dat"
if grep -q '\*\*\*ERROR' "P171_MECHANICAL_DC.dat"; then echo "MECHANICAL DATACHECK ERROR"; exit 66; fi
echo "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Phase Subproblem Datacheck ==="
abaqus job=P171_PHASE_DC user=f42_mixed_uel.for input=P171_PHASE_DC.inp cpus=1 memory="8 gb" datacheck interactive > P171_PHASE_DC.stdout.txt 2>&1
test -f "P171_PHASE_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P171_PHASE_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P171_PHASE_DC.dat"
if grep -q '\*\*\*ERROR' "P171_PHASE_DC.dat"; then echo "PHASE DATACHECK ERROR"; exit 67; fi
echo "P171_PHASE_DC: AUTHENTIC_DATACHECK_PASS"
