#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_pk_f1714_five_hole

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Starting Abaqus 2023 Datacheck with f42_amor_split_uel.for ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

# Clean any existing M1_PK_F1714_AMOR_DATACHECK files
rm -f M1_PK_F1714_AMOR_DATACHECK.*

set +e
abaqus job=M1_PK_F1714_AMOR_DATACHECK input=PK_F1714_JOB2_ADAPTED_PROD.inp user=f42_amor_split_uel.for datacheck interactive
EXIT_CODE=$?
set -e

echo "=== Datacheck Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
