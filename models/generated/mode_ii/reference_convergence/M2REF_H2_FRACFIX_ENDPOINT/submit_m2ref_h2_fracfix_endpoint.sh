#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

# Guarded submission wrapper for the single H2 endpoint-resolution job.
# This package is preparation-only until a direct human authorization is recorded.

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${PACKAGE_DIR}/../../../../.." && pwd)"
AUTH_FILE="${PACKAGE_DIR}/H2_ENDPOINT_SUBMISSION_AUTHORIZATION.json"
PREFLIGHT="${PROJECT_ROOT}/scripts/validation/validate_h2_endpoint_extension_preflight.py"

if [[ ! -f "${AUTH_FILE}" ]]; then
    echo "ERROR: direct human authorization record missing: ${AUTH_FILE}" >&2
    exit 1
fi

python3 "${PREFLIGHT}" --authorization "${AUTH_FILE}"
cd "${PACKAGE_DIR}"
qsub M2REF_H2_FRACFIX_ENDPOINT.pbs
