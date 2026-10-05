#!/usr/bin/env bash
# Guarded Submission Wrapper for Production Candidate M2STATE_FRACFIX_RESTART1R1R6R2
# Candidate Revision: M2STATE_FRACFIX_RESTART1R1R6R2
# Author: Gemini Antigravity
# Protocol Version: 1

set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_MANIFEST="${SCRIPT_DIR}/PACKAGE_MANIFEST.json"
PBS_SCRIPT="${SCRIPT_DIR}/M2STATE_FRACFIX_RESTART1R1R6R2.pbs"
CANDIDATE_NAME="M2STATE_FRACFIX_RESTART1R1R6R2"

DRY_RUN=false
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    fi
done

echo "======================================================================"
echo "[PREFLIGHT] Validating package integrity for ${CANDIDATE_NAME}..."
echo "======================================================================"

if [[ ! -f "${PACKAGE_MANIFEST}" ]]; then
    echo "[PREFLIGHT] ERROR: Manifest file missing: ${PACKAGE_MANIFEST}" >&2
    exit 1
fi

if [[ ! -f "${PBS_SCRIPT}" ]]; then
    echo "[PREFLIGHT] ERROR: PBS script missing: ${PBS_SCRIPT}" >&2
    exit 1
fi

NOTIF_HELPER="${SCRIPT_DIR}/job_notifications.sh"
if [[ ! -f "${NOTIF_HELPER}" ]]; then
    NOTIF_HELPER="${HOME}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
fi

if [[ -f "${NOTIF_HELPER}" ]]; then
    source "${NOTIF_HELPER}"
fi

echo "[PREFLIGHT] Checking package execution files..."
for f in "M2STATE_FRACFIX_RESTART1R1R6R2.inp" "f42_mixed_uel.for" "STATE_TRANSFER_ARTIFACT.json" "TRANSFER_MANIFEST.json" "RESTART_ACCEPTANCE_CONTRACT.json" "job_notifications.sh" "validate_package_manifest.py" "extract_restart1r1r6_odb.py" "verify_restart1r1r6_science.py"; do
    if [[ ! -f "${SCRIPT_DIR}/${f}" ]]; then
        echo "[PREFLIGHT] ERROR: Required candidate file missing: ${f}" >&2
        exit 1
    fi
done

# Run standalone validator
python3 "${SCRIPT_DIR}/validate_package_manifest.py" "${PACKAGE_MANIFEST}"
echo "[PREFLIGHT] Package files present and verified."

if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[PREFLIGHT] Dry-run verification PASS."
    echo "[PREFLIGHT] Intended command: qsub ${PBS_SCRIPT}"
    echo "[PREFLIGHT] No qsub invoked during dry run."
    exit 0
fi

echo "======================================================================"
echo "[SUBMIT] Submitting ${CANDIDATE_NAME} to PBS scheduler..."
echo "======================================================================"

QSUB_BIN="qsub"
if [[ -n "${MOCK_QSUB_BIN:-}" ]]; then
    QSUB_BIN="${MOCK_QSUB_BIN}"
fi

JOB_OUTPUT=$("${QSUB_BIN}" "${PBS_SCRIPT}")
JOB_ID=$(echo "${JOB_OUTPUT}" | tail -n 1)

echo "[SUBMIT] SUCCESS: Job submitted as ${JOB_ID}"

if declare -f notify_submitted >/dev/null 2>&1; then
    notify_submitted "${JOB_ID}" "${CANDIDATE_NAME}" "Submitted to PBS queue entry_imfdfkmq (1 CPU, 8GB, 24:00:00)" || echo "[SUBMIT] WARNING: Submission notification delivery failed" >&2
elif declare -f notify_event >/dev/null 2>&1; then
    notify_event "SUBMITTED" "${JOB_ID}" "${CANDIDATE_NAME}" "Submitted to PBS queue entry_imfdfkmq" || echo "[SUBMIT] WARNING: Submission notification delivery failed" >&2
fi

exit 0
