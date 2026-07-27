#!/bin/bash
# Stage F Mode-II H0 endpoint-corrected datacheck submission wrapper.
# Guarded submission wrapper: defaults to preflight only; requires explicit authorization file and environment flag.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AUTH_FILE="${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json"
PBS_SCRIPT="${ROOT_DIR}/scripts/hpc/stage_f/03_mode_ii_h0_endpoint_corrected_datacheck.pbs"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"

echo "Mode-II H0 Endpoint-Corrected Datacheck Wrapper (Guarded)"

if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: Authorization file missing: ${AUTH_FILE}"
  exit 1
fi

DATACHECK_AUTH="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('datacheck_authorized', False)).lower())" 2>/dev/null || echo "false")"
DATACHECK_USED="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('datacheck_submissions_used', 1))" 2>/dev/null || echo "1")"
SUBMISSION_APPROVED="$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('submission_approved', False)).lower())" 2>/dev/null || echo "false")"
ALLOW_SUBMIT="${ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT:-0}"

if [ "${DATACHECK_AUTH}" != "true" ] || [ "${DATACHECK_USED}" -ge 1 ] || [ "${SUBMISSION_APPROVED}" != "true" ] || [ "${ALLOW_SUBMIT}" != "1" ]; then
  echo "Preflight check PASS (Submission NOT authorized)."
  echo "datacheck_authorized: ${DATACHECK_AUTH}"
  echo "datacheck_submissions_used: ${DATACHECK_USED}"
  echo "submission_approved: ${SUBMISSION_APPROVED}"
  echo "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT: ${ALLOW_SUBMIT}"
  exit 0
fi

cd "${ROOT_DIR}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7

echo "Executing guarded datacheck submission..."
JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name mode_ii_h0_endpoint_corrected_datacheck \
  --message "Stage F1-C2 Mode-II H0 endpoint-corrected datacheck; 1 rank x 1 thread; one-shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  "${PBS_SCRIPT}")"

if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "ERROR: Datacheck qsub returned invalid job ID: ${JOB_ID}" >&2
  exit 22
fi

echo "Submitted datacheck PBS Job ID: ${JOB_ID}"
