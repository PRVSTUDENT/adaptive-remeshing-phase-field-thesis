#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_pk_f1716_five_hole_checkpoint"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Starting F1716 5-Hole Production Checkpoint (Single-Rank Serial) ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
START_TIME=$(date +%s%N)

set +e
abaqus job=PK_F1716_CHECKPOINT_SERIAL input=PK_F1716_CHECKPOINT.inp user=f42_amor_split_uel_v2.for cpus=1 interactive
EXIT_CODE=$?
set -e

END_TIME=$(date +%s%N)
ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))

echo "=== Abaqus Finished with Exit Code: ${EXIT_CODE} ==="
echo "Elapsed Time: ${ELAPSED_MS} ms"
date -u +"%Y-%m-%dT%H:%M:%SZ"

exit ${EXIT_CODE}
