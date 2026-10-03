#!/bin/bash
set -euo pipefail

WORKDIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906"
cd "${WORKDIR}"

if [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh
fi

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING DIRECT SERIAL SOLVE PK_M1_JOB1_INF_COMPANION_2906 ==="
abaqus job=PK_M1_JOB1_INF_COMPANION_2906 input=PK_M1_JOB1_INF_COMPANION_2906.inp user=f42_mixed_uel_inf_stress.for cpus=1 double=both ask_delete=OFF interactive
ABAQUS_EXIT=$?
echo "=== FINISHED DIRECT SERIAL SOLVE PK_M1_JOB1_INF_COMPANION_2906 (EXIT: $ABAQUS_EXIT) ==="
exit "$ABAQUS_EXIT"
