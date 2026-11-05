#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

echo "=== Package 171-R12 Abaqus 2023 Datachecks ==="

# 1. Preliminary Mechanical Datacheck
echo "Running Preliminary Mechanical Datacheck..."
abaqus job=P171_MECHANICAL_DC input=P171_MECHANICAL_DC.inp user=f42_mixed_uel.for datacheck interactive cpus=1 memory="16 gb" > P171_MECHANICAL_DC.stdout.txt 2>&1
if grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" P171_MECHANICAL_DC.dat || grep -q "ANALYSIS DATACHECK COMPLETE" P171_MECHANICAL_DC.dat; then
    echo "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS"
else
    echo "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_FAIL"
    exit 1
fi

# 2. Preliminary Phase Datacheck
echo "Running Preliminary Phase Datacheck..."
abaqus job=P171_PHASE_DC input=P171_PHASE_DC.inp user=f42_mixed_uel.for datacheck interactive cpus=1 memory="16 gb" > P171_PHASE_DC.stdout.txt 2>&1
if grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" P171_PHASE_DC.dat || grep -q "ANALYSIS DATACHECK COMPLETE" P171_PHASE_DC.dat; then
    echo "P171_PHASE_DC: AUTHENTIC_DATACHECK_PASS"
else
    echo "P171_PHASE_DC: AUTHENTIC_DATACHECK_FAIL"
    exit 1
fi

# 3. Dynamic Iteration 1 Mechanical Datacheck
echo "Running Dynamic Iteration 1 Mechanical Datacheck..."
abaqus job=P171_ITER1_MECH input=P171_ITER1_MECH.inp user=f42_mixed_uel.for datacheck interactive cpus=1 memory="16 gb" > P171_ITER1_MECH.stdout.txt 2>&1
if grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" P171_ITER1_MECH.dat || grep -q "ANALYSIS DATACHECK COMPLETE" P171_ITER1_MECH.dat; then
    echo "P171_ITER1_MECH: AUTHENTIC_DATACHECK_PASS"
else
    echo "P171_ITER1_MECH: AUTHENTIC_DATACHECK_FAIL"
    exit 1
fi

# 4. Dynamic Iteration 1 Phase Datacheck
echo "Running Dynamic Iteration 1 Phase Datacheck..."
abaqus job=P171_ITER1_PHASE input=P171_ITER1_PHASE.inp user=f42_mixed_uel.for datacheck interactive cpus=1 memory="16 gb" > P171_ITER1_PHASE.stdout.txt 2>&1
if grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" P171_ITER1_PHASE.dat || grep -q "ANALYSIS DATACHECK COMPLETE" P171_ITER1_PHASE.dat; then
    echo "P171_ITER1_PHASE: AUTHENTIC_DATACHECK_PASS"
else
    echo "P171_ITER1_PHASE: AUTHENTIC_DATACHECK_FAIL"
    exit 1
fi

echo "All 4 Package 171-R12 Datachecks Completed Successfully with Exit 0!"

