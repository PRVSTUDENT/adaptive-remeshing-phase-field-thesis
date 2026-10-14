#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_c1_forward_refinement"
cd "${RUN_DIR}"

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

JOB_NAME="M1_MC_C1_FWD_DC"
INP_NAME="M1_MC_C1_FORWARD_14K.inp"
USER_SUB="f42_mixed_uel.for"

rm -f "${JOB_NAME}.lck" "${JOB_NAME}.023" "${JOB_NAME}.dat" "${JOB_NAME}.msg" "${JOB_NAME}.log" 2>/dev/null || true

echo "Running Abaqus 2023 Datacheck with Intel Fortran compilation..."
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" datacheck interactive
EXIT_CODE=$?

echo "Datacheck Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
