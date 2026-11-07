#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_datacheck

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Starting Abaqus 2023 Datacheck for M1_HOLE_F1664_METHOD_A_DATACHECK ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
command -v ifort

export JOB_NAME="M1_HOLE_F1664_METHOD_A_DATACHECK"
test ! -e "${JOB_NAME}.lck"

abaqus job="${JOB_NAME}" input="PK_HOLE_F1664_METHOD_A_PROD.inp" user="f42_mixed_uel.for" datacheck interactive
EXIT_CODE=$?

echo "=== Datacheck Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
