#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "${PACKAGE_DIR}"

if [ "${F43DRY_PK5_AUTHORIZED:-0}" -ne 1 ]; then
    echo "ERROR: Submission unauthorized. Must explicitly set F43DRY_PK5_AUTHORIZED=1" >&2
    exit 1
fi

qsub -v F43DRY_PK5_WRAPPER_AUTHORIZED=1 F43DRY_PK5.pbs
