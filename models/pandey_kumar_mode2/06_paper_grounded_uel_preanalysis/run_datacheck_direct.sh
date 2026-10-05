#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis || exit 1

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING DIRECT DATACHECK FOR MODE-II JOB-1_UEL ==="
rm -f M2_J1_DATACHECK.lck M2_J1_DATACHECK.023
abaqus job=M2_J1_DATACHECK user=f42_mixed_uel.for input=Job-1_UEL.inp cpus=1 datacheck interactive
ABAQUS_EXIT=$?
echo "=== DIRECT DATACHECK COMPLETED WITH EXIT: $ABAQUS_EXIT ==="
exit "$ABAQUS_EXIT"
