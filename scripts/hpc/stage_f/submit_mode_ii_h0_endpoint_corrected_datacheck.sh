#!/bin/bash
# Stage F Mode-II H0 endpoint-corrected datacheck submission wrapper.
# Guarded submission wrapper: defaults to preflight only; requires explicit authorization file and environment flag.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AUTH_FILE="${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json"
PBS_SCRIPT="${ROOT_DIR}/scripts/hpc/stage_f/03_mode_ii_h0_endpoint_corrected_datacheck.pbs"

echo "Mode-II H0 Endpoint-Corrected Datacheck Wrapper (Guarded)"

if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: Authorization file missing: ${AUTH_FILE}"
  exit 1
fi

DATACHECK_AUTH="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('datacheck_authorized', False)).lower())" 2>/dev/null || echo "false")"
DATACHECK_USED="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('datacheck_submissions_used', 1))" 2>/dev/null || echo "1")"
ALLOW_SUBMIT="${ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT:-0}"

if [ "${DATACHECK_AUTH}" != "true" ] || [ "${DATACHECK_USED}" -ge 1 ] || [ "${ALLOW_SUBMIT}" != "1" ]; then
  echo "Preflight check PASS (Submission NOT authorized)."
  echo "datacheck_authorized: ${DATACHECK_AUTH}"
  echo "datacheck_submissions_used: ${DATACHECK_USED}"
  echo "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT: ${ALLOW_SUBMIT}"
  exit 0
fi

echo "ERROR: Active submission execution is not authorized in task F1-C1-CORRECTED-H0-PREP."
exit 2
