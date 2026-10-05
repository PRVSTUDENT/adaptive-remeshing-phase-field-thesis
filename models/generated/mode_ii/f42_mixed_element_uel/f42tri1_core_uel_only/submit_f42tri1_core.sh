#!/bin/bash
# Guarded Submission Wrapper for F42TRI1_CORE
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [ "${1:-}" != "--authorize-execution" ]; then
    echo "ERROR: Submission not authorized. Requires explicit --authorize-execution flag." >&2
    echo "Current authorization status: execution_authorized = false" >&2
    exit 1
fi

export F42TRI1_CORE_WRAPPER_AUTHORIZED=1
qsub F42TRI1_CORE.pbs
