#!/bin/bash
set -e
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/30_stage14_adaptive_candidate_spatial_fine
source /etc/profile.d/modules.sh 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || true

rm -f PK_M1_14AM_DATACHECK.lck PK_M1_14AM_DATACHECK.023
echo "Running direct datacheck on cluster login node for Package 30..."
/cluster/application/abaqus/2023/Commands/abaqus datacheck job=PK_M1_14AM_DATACHECK input=PK_M1_14AM_DATACHECK.inp user=f42_mixed_uel.for memory="16gb" double=both interactive
echo "Datacheck completed with exit code $?"
