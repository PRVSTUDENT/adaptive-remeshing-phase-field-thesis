#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

# Guarded submission wrapper for M2REF_H0_EXACT_FRACFIX_REPRO
# Protocol version: 1
# Requires explicit prior human chat authorization.

AUTH_FILE="../VERIFICATION_BATCH_SUBMISSION_RECORD.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2
    exit 1
fi

echo "Submitting M2REF_H0_EXACT_FRACFIX_REPRO to PBS..."
qsub M2REF_H0_EXACT_FRACFIX_REPRO.pbs
