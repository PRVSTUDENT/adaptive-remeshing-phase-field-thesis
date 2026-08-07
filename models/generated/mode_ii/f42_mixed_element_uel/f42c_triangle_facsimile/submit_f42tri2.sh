#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for F42TRI2
EXECUTION_AUTHORIZED="${F42TRI2_EXECUTION_AUTHORIZED:-false}"

if [ "${EXECUTION_AUTHORIZED}" != "true" ]; then
    echo "ERROR: Execution not authorized. Set F42TRI2_EXECUTION_AUTHORIZED=true after human approval." >&2
    exit 1
fi

export F42TRI2_WRAPPER_AUTHORIZED=1
qsub -v F42TRI2_WRAPPER_AUTHORIZED=1 F42TRI2.pbs
