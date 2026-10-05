#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

# Guarded submission wrapper for F43PRE1
if [ "${F43PRE1_EXECUTION_AUTHORIZED:-false}" != "true" ]; then
    echo "ERROR: Execution not authorized in ACTIVE_TASK.json" >&2
    exit 1
fi

qsub -v F43PRE1_WRAPPER_AUTHORIZED=1 F43PRE1.pbs
