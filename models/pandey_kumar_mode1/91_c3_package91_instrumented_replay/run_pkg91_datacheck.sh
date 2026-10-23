#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package91_c3_instrumented_replay"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

JOB_NAME="M1_C3_PACKAGE91_INSTRUMENTED_REPLAY_DC"
INP_NAME="M1_C3_PACKAGE91_INSTRUMENTED_REPLAY.inp"
USER_SUB="f42_mixed_uel.for"

echo "Starting Datacheck ${JOB_NAME} at $(date)"
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" datacheck interactive
EXIT_CODE=$?
echo "Datacheck completed with exit code ${EXIT_CODE} at $(date)"
exit ${EXIT_CODE}
