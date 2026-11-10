#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_pk_f1713_job2_adapted

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Starting Abaqus 2023 Datacheck for M1_PK_F1713_DATACHECK ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

set +e
abaqus job=M1_PK_F1713_DATACHECK input=PK_F1713_JOB2_ADAPTED_PROD.inp user=f42_mixed_uel.for datacheck interactive
EXIT_CODE=$?
set -e

echo "=== Datacheck Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
