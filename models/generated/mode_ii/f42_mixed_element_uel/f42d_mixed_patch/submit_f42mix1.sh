#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for F42MIX1
if [ "${F42MIX1_EXECUTION_AUTHORIZED:-false}" != "true" ]; then
    echo "ERROR: Execution not authorized in ACTIVE_TASK.json" >&2
    exit 1
fi

qsub -v F42MIX1_WRAPPER_AUTHORIZED=1 F42MIX1.pbs
