#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_prod"
cd "${RUN_DIR}"

export JOB_NAME="M1_HOLE_F1664_METHOD_A_PROD"
export INP_NAME="PK_HOLE_F1664_METHOD_A_PROD.inp"
export USER_SUB="f42_mixed_uel.for"

EXPECTED_INP_SHA="b6fb9ad2c16293e78e0940c00c65d9d54c3921e8234ceb770956117d6b39d99b"
EXPECTED_UEL_SHA="ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

echo "=== Preflight Hash Verification for ${JOB_NAME} ==="
test ! -e "${JOB_NAME}.lck"
ACTUAL_INP_SHA=$(sha256sum "${INP_NAME}" | awk '{print $1}')
ACTUAL_UEL_SHA=$(sha256sum "${USER_SUB}" | awk '{print $1}')
test "${ACTUAL_INP_SHA}" = "${EXPECTED_INP_SHA}"
test "${ACTUAL_UEL_SHA}" = "${EXPECTED_UEL_SHA}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Starting Abaqus 2023 Method A Production Fracture Run ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
command -v ifort
command -v abaqus

abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" interactive
EXIT_CODE=$?

echo "=== Fracture Simulation Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
