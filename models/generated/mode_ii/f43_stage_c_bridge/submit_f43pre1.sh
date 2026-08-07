#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for F43PRE1
if [ "${F43PRE1_EXECUTION_AUTHORIZED:-false}" != "true" ]; then
    echo "ERROR: Execution not authorized in ACTIVE_TASK.json" >&2
    exit 1
fi

qsub -v F43PRE1_WRAPPER_AUTHORIZED=1 F43PRE1.pbs
