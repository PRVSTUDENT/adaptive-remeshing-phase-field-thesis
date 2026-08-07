#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for F43REM1-R1 Current Predecessor
if ! command -v qsub >/dev/null 2>&1; then
    echo "ERROR: qsub command not found. Must be executed on TU Freiberg HPC cluster environment." >&2
    exit 1
fi

if [ "${F43REM1_EXECUTION_AUTHORIZED:-false}" != "true" ]; then
    echo "ERROR: Execution not authorized in ACTIVE_TASK.json" >&2
    exit 1
fi

SOURCE_ODB="${PBS_O_WORKDIR:-.}/evidence/1384674.mmaster02/F43PRE1.odb"
EXPECTED_SHA256="3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534"

if [ ! -f "${SOURCE_ODB}" ]; then
    SOURCE_ODB="/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1384674.mmaster02/F43PRE1.odb"
fi

if [ ! -f "${SOURCE_ODB}" ]; then
    echo "ERROR: Source predecessor ODB not found: ${SOURCE_ODB}" >&2
    exit 1
fi

ACTUAL_SHA256="$(sha256sum "${SOURCE_ODB}" | awk '{print $1}')"
if [ "${ACTUAL_SHA256}" != "${EXPECTED_SHA256}" ]; then
    echo "ERROR: Source ODB SHA256 mismatch. Expected: ${EXPECTED_SHA256}, Actual: ${ACTUAL_SHA256}" >&2
    exit 1
fi

if qstat -u "$(whoami)" 2>/dev/null | grep -q "F43REM1"; then
    echo "ERROR: Duplicate F43REM1 job already queued or running." >&2
    exit 1
fi

QSUB_OUT="$(qsub -v F43REM1_WRAPPER_AUTHORIZED=1 F43REM1.pbs)"
QSUB_RC=$?

if [ $QSUB_RC -ne 0 ] || [ -z "${QSUB_OUT}" ]; then
    echo "ERROR: qsub failed with return code ${QSUB_RC}" >&2
    exit 1
fi

echo "SUCCESS: Job submitted with ID ${QSUB_OUT}"
