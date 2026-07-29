#!/usr/bin/env bash
# Submit wrapper for Stage F Candidate Job B (Pandey-Kumar MISESERI pre-analysis).
# Defaults to preflight-only unless --submit or MODE_II_MISESERI_SUBMIT=1 is provided.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

SUBMIT=false
if [ "${MODE_II_MISESERI_SUBMIT:-0}" = "1" ]; then
  SUBMIT=true
fi

for arg in "$@"; do
  if [ "${arg}" = "--submit" ]; then
    SUBMIT=true
  fi
done

AUTH_FILE="${PROJECT_ROOT}/runs/hpc/stage_f/MODE_II_STAGE_F3_AUTHORIZATION_PROPOSAL.json"
if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: authorization file missing: ${AUTH_FILE}" >&2
  exit 1
fi

echo "Preflight check for Candidate Job B (Pandey-Kumar MISESERI pre-analysis):"
echo "  Authorization file: ${AUTH_FILE}"
echo "  Submit requested: ${SUBMIT}"

if [ "${SUBMIT}" != "true" ]; then
  echo "  QSUB count: 0 (preflight mode active)"
  exit 0
fi

# Validation when submission is requested
python3 -c "
import json, sys
auth = json.load(open('${AUTH_FILE}'))
checks = [
    auth.get('execution_authorized') is True,
    auth.get('submission_approved') is True,
    auth.get('maximum_jobs_now', 0) > 0,
]
if not all(checks):
    print(f'ERROR: Authorization proposal preflight checks failed: {auth}', file=sys.stderr)
    sys.exit(2)
"

JOB_NAME="mode_ii_miseseri_preanalysis"
if command -v qstat >/dev/null 2>&1; then
  if qstat -u "$USER" 2>/dev/null | grep -q "${JOB_NAME}"; then
    echo "ERROR: Duplicate job already active in qstat: ${JOB_NAME}" >&2
    exit 3
  fi
fi

PBS_SCRIPT="${SCRIPT_DIR}/mode_ii_miseseri_preanalysis.pbs"
if [ ! -f "${PBS_SCRIPT}" ]; then
  echo "ERROR: PBS script missing: ${PBS_SCRIPT}" >&2
  exit 4
fi

SUBMIT_NOTIFY="${PROJECT_ROOT}/scripts/hpc/qsub_with_submitted_notify.sh"

echo "Authorization verified. Submitting Candidate Job B (Pandey-Kumar MISESERI pre-analysis)..."

PROJECT_REVISION="$(git -C "${PROJECT_ROOT}" rev-parse HEAD 2>/dev/null || echo "unknown")"
PRESTAGED_ROOT="${PROJECT_ROOT}"
PRESTAGED_RUNTIME_ROOT="${PROJECT_ROOT}"

if [ -f "${SUBMIT_NOTIFY}" ]; then
  bash "${SUBMIT_NOTIFY}" \
    --job-name "${JOB_NAME}" \
    --message "Queue: entry_imfdfkmq; CPUs: 1; memory: 16 GB; walltime: 01:00:00" \
    -- \
    -v "PROJECT_REVISION=${PROJECT_REVISION},PRESTAGED_ROOT=${PRESTAGED_ROOT},PRESTAGED_RUNTIME_ROOT=${PRESTAGED_RUNTIME_ROOT}" \
    "${PBS_SCRIPT}"
else
  qsub -v "PROJECT_REVISION=${PROJECT_REVISION},PRESTAGED_ROOT=${PRESTAGED_ROOT},PRESTAGED_RUNTIME_ROOT=${PRESTAGED_RUNTIME_ROOT}" "${PBS_SCRIPT}"
fi
