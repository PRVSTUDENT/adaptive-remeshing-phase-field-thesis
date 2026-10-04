#!/bin/bash
source /etc/profile
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x
rm -f PK_M1_14K_TEMPORAL_2X_DATACHECK.lck PK_M1_14K_TEMPORAL_2X_DATACHECK.023
abaqus datacheck job=PK_M1_14K_TEMPORAL_2X_DATACHECK user=f42_mixed_uel.for input=PK_M1_14K_TEMPORAL_2X_DATACHECK.inp cpus=1 interactive
ABAQUS_EXIT=$?
echo "=== DATACHECK_FINISHED_EXIT_CODE: $ABAQUS_EXIT ==="
exit "$ABAQUS_EXIT"
