#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for F43PRE2_GEOM
if [ "${F43PRE2_GEOM_EXECUTION_AUTHORIZED:-false}" != "true" ]; then
    echo "ERROR: Execution not authorized in ACTIVE_TASK.json" >&2
    exit 1
fi

qsub -v F43PRE2_GEOM_WRAPPER_AUTHORIZED=1 F43PRE2_GEOM.pbs
