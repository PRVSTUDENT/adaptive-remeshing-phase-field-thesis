#!/bin/bash
set -euo pipefail
WORK_DIR="/scratch9/pr21vyci/runs/mode1_c3_companion_miseseri"
mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

if [ ! -f "M1_C3_COMPANION_FRAME6.odb" ]; then
    echo "Starting Abaqus companion linear elastic solve: M1_C3_COMPANION_FRAME6..."
    abaqus job=M1_C3_COMPANION_FRAME6 input=M1_C3_COMPANION_FRAME6.inp cpus=1 interactive
    SOLVER_EXIT=$?
    echo "Abaqus completed with exit code: ${SOLVER_EXIT}"
    if [ ${SOLVER_EXIT} -ne 0 ]; then
        echo "ERROR: Companion solve failed!"
        exit ${SOLVER_EXIT}
    fi
fi

echo "Extracting authentic MISESERI distribution..."
abaqus python extract_c3_miseseri_distribution.py
EXTRACT_EXIT=$?
echo "Extraction completed with exit code: ${EXTRACT_EXIT}"

exit ${EXTRACT_EXIT}
