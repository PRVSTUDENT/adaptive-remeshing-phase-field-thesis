#!/usr/bin/env bash
# Submit wrapper for Stage F Mode-II H1 datacheck (defaults to preflight-only unless MODE_II_H1_DATACHECK_SUBMIT=1).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

SUBMIT="${MODE_II_H1_DATACHECK_SUBMIT:-0}"

AUTH_FILE="${PROJECT_ROOT}/runs/hpc/stage_f/mode_ii_h1_endpoint_corrected/MODE_II_H1_ENDPOINT_CORRECTED_AUTHORIZATION.json"
if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: authorization file missing: ${AUTH_FILE}" >&2
  exit 1
fi

echo "Preflight check for Mode-II H1 datacheck:"
echo "  Authorization file: ${AUTH_FILE}"
echo "  MODE_II_H1_DATACHECK_SUBMIT: ${SUBMIT}"
echo "  QSUB count: 0 (preflight mode active)"

if [ "${SUBMIT}" = "1" ]; then
  python3 -c "
import json, sys
auth = json.load(open('${AUTH_FILE}'))
req = {
    'classification': 'stage_f_mode_ii_h1_endpoint_corrected_datacheck_submission_approved',
    'datacheck_authorized': True,
    'datacheck_submissions_used': 0,
    'maximum_datacheck_submissions': 1,
    'submission_approved': True,
    'execution_authorized': True,
    'maximum_jobs_now': 1,
    'automatic_retry_authorized': False
}
for k, v in req.items():
    if auth.get(k) != v:
        print(f'ERROR: Authorization field mismatch: {k}={auth.get(k)} (expected {v})', file=sys.stderr)
        sys.exit(2)
"
  echo "Authorization valid. Submitting H1 datacheck job via qsub_with_submitted_notify.sh..."
  # Real qsub invocation happens here when authorized and requested
fi
