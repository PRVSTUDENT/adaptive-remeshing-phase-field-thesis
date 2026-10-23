#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package94_c4_authentic_transfer"
cd "${RUN_DIR}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}"
mkdir -p "${XDG_RUNTIME_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="M1_C4_PACKAGE94_TRANSFER_DC"
INP_NAME="M1_C4_PACKAGE94_TRANSFER.inp"
USER_SUB="f42_mixed_uel.for"

rm -f ${JOB_NAME}.log ${JOB_NAME}.dat ${JOB_NAME}.msg ${JOB_NAME}.sta
echo "Starting Datacheck ${JOB_NAME} at $(date)"
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" datacheck interactive
EXIT_CODE=$?
echo "Datacheck completed with exit code ${EXIT_CODE} at $(date)"
exit ${EXIT_CODE}
