#!/bin/bash
set -euo pipefail

# Load environment
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

WORKDIR="/scratch9/pr21vyci/test_mode2_datacheck"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

cp /home/pr21vyci/projects/mode2_reproduction_worktree/models/pandey_kumar_mode2/f42_mixed_uel_mode2_miehe.for ./f42_mixed_uel_mode2_miehe.for
cp /home/pr21vyci/projects/mode2_reproduction_worktree/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL.inp ./Job-1_UEL.inp

echo "=== Running Abaqus Datacheck for Mode-II Job-1_UEL with Miehe UEL ==="
abaqus job=M2_J1_DATACHECK input=Job-1_UEL.inp user=f42_mixed_uel_mode2_miehe.for cpus=1 datacheck interactive

echo "DATACHECK_EXIT=$?"
if grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" M2_J1_DATACHECK.log M2_J1_DATACHECK.dat M2_J1_DATACHECK.msg 2>/dev/null; then
    echo "DATACHECK_STATUS=SUCCESS"
else
    echo "DATACHECK_STATUS=CHECK_LOGS"
    tail -n 25 M2_J1_DATACHECK.msg 2>/dev/null || true
    tail -n 25 M2_J1_DATACHECK.dat 2>/dev/null || true
fi
