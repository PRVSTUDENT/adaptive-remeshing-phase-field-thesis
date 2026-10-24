#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_experimental_diagnostic_patch"
cd "${RUN_DIR}"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}"
mkdir -p "${XDG_RUNTIME_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Starting Abaqus 2023 Datacheck on 4-Element Diagnostic..."
abaqus job=M1_DIAG_DC input=M1_DIAGNOSTIC_4ELEM_IRREV.inp user=f42_experimental_irreversible_uel.for datacheck interactive
EXIT_CODE=$?
echo "Datacheck finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
