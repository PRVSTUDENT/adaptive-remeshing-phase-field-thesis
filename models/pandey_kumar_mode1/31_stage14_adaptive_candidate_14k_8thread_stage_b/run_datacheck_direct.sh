#!/bin/bash
set -euo pipefail

cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/31_stage14_adaptive_candidate_14k_8thread_stage_b || exit 1

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING DIRECT DATACHECK FOR PACKAGE 31 (8 THREADS) ==="
rm -f PK_M1_14K_8T_STAGE_B_DATACHECK.*
abaqus job=PK_M1_14K_8T_STAGE_B_DATACHECK user=f42_mixed_uel.for input=PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp cpus=8 mp_mode=threads datacheck interactive
DC_EXIT=$?
echo "=== DATACHECK COMPLETED WITH EXIT: $DC_EXIT ==="
exit "$DC_EXIT"
