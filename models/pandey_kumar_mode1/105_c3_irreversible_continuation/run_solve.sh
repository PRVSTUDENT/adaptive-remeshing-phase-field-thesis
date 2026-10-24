#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")" || exit 1
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}"
mkdir -p "${XDG_RUNTIME_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Starting Abaqus 2023 Solve on Candidate C3 Continuation..."
abaqus job=M1_C3_IRREV_SOLVE input=M1_C3_IRREV_CONTINUATION.inp user=f42_experimental_irreversible_uel.for interactive
EXIT_CODE=$?
echo "Solve finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
