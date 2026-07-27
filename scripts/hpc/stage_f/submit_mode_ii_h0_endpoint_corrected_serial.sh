#!/bin/bash
# Stage F Mode-II H0 endpoint-corrected serial solver submission wrapper.
# Guarded submission wrapper: defaults to preflight only; requires explicit authorization file and environment flag.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AUTH_FILE="${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json"
PBS_SCRIPT="${ROOT_DIR}/scripts/hpc/stage_f/04_mode_ii_h0_endpoint_corrected_serial.pbs"

echo "Mode-II H0 Endpoint-Corrected Serial Solver Wrapper (Guarded)"

if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: Authorization file missing: ${AUTH_FILE}"
  exit 1
fi

SOLVER_AUTH="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('solver_authorized', False)).lower())" 2>/dev/null || echo "false")"
SOLVER_USED="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('solver_submissions_used', 1))" 2>/dev/null || echo "1")"
ALLOW_SUBMIT="${ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT:-0}"

if [ "${SOLVER_AUTH}" != "true" ] || [ "${SOLVER_USED}" -ge 1 ] || [ "${ALLOW_SUBMIT}" != "1" ]; then
  echo "Preflight check PASS (Submission NOT authorized)."
  echo "solver_authorized: ${SOLVER_AUTH}"
  echo "solver_submissions_used: ${SOLVER_USED}"
  echo "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT: ${ALLOW_SUBMIT}"
  exit 0
fi

echo "ERROR: Active submission execution is not authorized in task F1-C1-CORRECTED-H0-PREP."
exit 2
