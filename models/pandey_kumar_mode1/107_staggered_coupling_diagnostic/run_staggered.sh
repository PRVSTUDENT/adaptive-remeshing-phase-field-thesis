#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_turn122_staggered_diagnostic"
cd "${RUN_DIR}"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}"
mkdir -p "${XDG_RUNTIME_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== ABAQUS 2023 STAGGERED 2-STEP DATACHECK ==="
abaqus job=M1_DIAG_STAG_DC input=M1_DIAG_STAGGERED_2STEP.inp user=f42_experimental_irreversible_uel.for datacheck interactive
DC_EXIT=$?
echo "Datacheck exit code: ${DC_EXIT}"

if [ ${DC_EXIT} -ne 0 ]; then
  echo "Datacheck failed!"
  exit ${DC_EXIT}
fi

echo "=== ABAQUS 2023 STAGGERED 2-STEP SOLVER ==="
abaqus job=M1_DIAG_STAG_SOLVE input=M1_DIAG_STAGGERED_2STEP.inp user=f42_experimental_irreversible_uel.for interactive
SOLVE_EXIT=$?
echo "Solver exit code: ${SOLVE_EXIT}"
exit ${SOLVE_EXIT}
