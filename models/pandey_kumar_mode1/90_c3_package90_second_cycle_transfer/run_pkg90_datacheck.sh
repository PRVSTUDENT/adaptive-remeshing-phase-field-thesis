#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package90_c3_transfer"
cd "${RUN_DIR}"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}"
mkdir -p "${XDG_RUNTIME_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus Datacheck on M1_C3_PACKAGE90_TRANSFER.inp..."
rm -f M1_C3_PACKAGE90_TRANSFER_DC.lck M1_C3_PACKAGE90_TRANSFER_DC.log M1_C3_PACKAGE90_TRANSFER_DC.dat M1_C3_PACKAGE90_TRANSFER_DC.msg M1_C3_PACKAGE90_TRANSFER_DC.sta M1_C3_PACKAGE90_TRANSFER_DC.prt
abaqus datacheck job=M1_C3_PACKAGE90_TRANSFER_DC input=M1_C3_PACKAGE90_TRANSFER.inp user=f42_mixed_uel.for interactive
DC_EXIT=$?
echo "Datacheck finished with Exit Code: ${DC_EXIT}"
exit ${DC_EXIT}
