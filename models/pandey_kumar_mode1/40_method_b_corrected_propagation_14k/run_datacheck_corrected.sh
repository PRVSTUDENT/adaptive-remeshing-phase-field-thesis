#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_b_corrected_propagation_14k"
cd "${RUN_DIR}"

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

JOB_NAME="M1_MB_CORRECTED_14K_DC"
INP_NAME="M1_MB_CORRECTED_PROPAGATION_14K.inp"
USER_SUB="f42_mixed_uel.for"

rm -f "${JOB_NAME}.lck" "${JOB_NAME}.023" "${JOB_NAME}.log" "${JOB_NAME}.dat" "${JOB_NAME}.msg" "${JOB_NAME}.prt" "${JOB_NAME}.sta" 2>/dev/null || true

echo "=== RUNNING DATACHECK FOR M1_MB_CORRECTED_PROPAGATION_14K ==="
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" datacheck interactive

DC_EXIT=$?
echo "=== DATACHECK FINISHED WITH EXIT CODE: ${DC_EXIT} ==="
exit ${DC_EXIT}
