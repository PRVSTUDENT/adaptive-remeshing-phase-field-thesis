#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for F43REM1
if [ "${F43REM1_EXECUTION_AUTHORIZED:-false}" != "true" ]; then
    echo "ERROR: Execution not authorized in ACTIVE_TASK.json" >&2
    exit 1
fi

qsub -v F43REM1_WRAPPER_AUTHORIZED=1 F43REM1.pbs
