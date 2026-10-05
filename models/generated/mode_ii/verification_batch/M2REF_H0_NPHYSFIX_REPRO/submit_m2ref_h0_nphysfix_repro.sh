#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi
cd "$(dirname "$0")"

JOB_ID=$(qsub M2REF_H0_NPHYSFIX_REPRO.pbs)
echo "Submitted M2REF_H0_NPHYSFIX_REPRO under Job ID: $JOB_ID"
