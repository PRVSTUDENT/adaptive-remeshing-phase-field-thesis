#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_inc79_companion_miseseri"
cd "${RUN_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load abaqus/2023

JOB_NAME="M1_C4_INC79_COMPANION_DC"
INP_NAME="M1_C4_INC79_COMPANION.inp"

rm -f ${JOB_NAME}.log ${JOB_NAME}.dat ${JOB_NAME}.msg ${JOB_NAME}.sta
echo "Starting Datacheck ${JOB_NAME} at $(date)"
abaqus job="${JOB_NAME}" input="${INP_NAME}" datacheck interactive
EXIT_CODE=$?
echo "Datacheck completed with exit code ${EXIT_CODE} at $(date)"
exit ${EXIT_CODE}
