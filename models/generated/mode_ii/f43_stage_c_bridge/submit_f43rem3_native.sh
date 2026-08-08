#!/bin/bash
# Guarded submission wrapper for F43REM3_NATIVE native adaptive remeshing job
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

EXPECTED_PREP_SHA="${EXPECTED_PREP_SHA:-b03fa144d2aeabf30b48df52b5825a10a41afef2}"
EXPECTED_QUAL_SHA="${EXPECTED_QUAL_SHA:-f053342f031ea8feb27e7eb09b8d0a9095f59281}"
EXPECTED_CAE_SHA="0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"
EXPECTED_PRED_ODB_SHA="9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1"
EXTERNAL_CAE_PATH="/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre3/ModeII_Geometry_Source_Abaqus2023.cae"

echo "[F43REM3 Wrapper] Pre-flight verification..."

if [ "${F43REM3_SUBMISSION_APPROVED:-0}" -ne 1 ] && [ "${REPLACEMENT_AUTHORIZED:-0}" -ne 1 ]; then
    echo "FATAL ERROR: F43REM3_NATIVE submission not authorized by explicit human approval!" >&2
    exit 1
fi

REPLACEMENT_AUTHORIZED="${REPLACEMENT_AUTHORIZED:-0}"

MAX_SUBMISSIONS="${MAX_SUBMISSIONS:-0}"
if [ "${MAX_SUBMISSIONS}" -ne 1 ]; then
    echo "FATAL ERROR: MAX_SUBMISSIONS must equal 1! Got ${MAX_SUBMISSIONS}" >&2
    exit 1
fi

if [ "${AUTOMATIC_RETRY:-false}" = "true" ]; then
    echo "FATAL ERROR: Automatic retry is strictly prohibited!" >&2
    exit 1
fi

# Verify local required files in SCRIPT_DIR
for required_file in "F43REM3_NATIVE.pbs" "remesh_mode_ii_native_cae.py" "collect_f43rem3_native_evidence.sh" "validate_f43rem3_native.py"; do
    if [ ! -f "${SCRIPT_DIR}/${required_file}" ]; then
        echo "FATAL ERROR: Package file ${required_file} missing in ${SCRIPT_DIR}!" >&2
        exit 1
    fi
done

# Verify external CAE SHA on cluster if present
if [ -f "${EXTERNAL_CAE_PATH}" ]; then
    ACTUAL_CAE_SHA=$(sha256sum "${EXTERNAL_CAE_PATH}" | awk '{print $1}')
    if [ "${ACTUAL_CAE_SHA}" != "${EXPECTED_CAE_SHA}" ]; then
        echo "FATAL ERROR: External CAE SHA mismatch! Expected ${EXPECTED_CAE_SHA}, got ${ACTUAL_CAE_SHA}" >&2
        exit 1
    fi
fi

# Verify predecessor ODB SHA if present
PRED_ODB_PATH="${SCRIPT_DIR}/evidence/1385461.mmaster02/F43PRE3_GEOM.odb"
if [ -f "${PRED_ODB_PATH}" ]; then
    ACTUAL_PRED_ODB_SHA=$(sha256sum "${PRED_ODB_PATH}" | awk '{print $1}')
    if [ "${ACTUAL_PRED_ODB_SHA}" != "${EXPECTED_PRED_ODB_SHA}" ]; then
        echo "FATAL ERROR: Predecessor ODB SHA mismatch! Expected ${EXPECTED_PRED_ODB_SHA}, got ${ACTUAL_PRED_ODB_SHA}" >&2
        exit 1
    fi
fi

# Determine email recipients for PBS mail options
EMAIL_RECIPIENTS="${F40_NOTIFICATION_EMAIL_RECIPIENTS:-pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"

# Verify qstat
if ! qstat_out=$(qstat -u "$USER" 2>&1); then
    echo "FATAL ERROR: qstat check failed!" >&2
    exit 1
fi

if echo "$qstat_out" | grep -q "F43REM3_NATIVE"; then
    echo "FATAL ERROR: F43REM3_NATIVE job is already running or queued in qstat!" >&2
    exit 1
fi

echo "[F43REM3 Wrapper] All pre-flight checks passed."

cd "${SCRIPT_DIR}"
if [ "$(pwd)" != "${SCRIPT_DIR}" ]; then
    echo "FATAL ERROR: Failed to change working directory to ${SCRIPT_DIR}!" >&2
    exit 1
fi

if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[F43REM3 Wrapper] DRY_RUN=1: qsub call skipped."
    exit 0
fi

# Submit job with explicit PBS mail options
job_id=$(qsub -m abe -M "${EMAIL_RECIPIENTS}" "${SCRIPT_DIR}/F43REM3_NATIVE.pbs")
echo "[F43REM3 Wrapper] Submitted job ID: ${job_id}"

# Verify scheduler mail settings immediately via qstat -f
echo "[F43REM3 Wrapper] Verifying scheduler mail settings via qstat..."
qstat_full=$(qstat -f "${job_id}" 2>&1 || true)
echo "${qstat_full}" | grep -E "Mail_Users|Mail_Points|job_state" || true

# Dispatch submission notification (Telegram + Email)
NOTIFY_PY="${REPO_ROOT}/scripts/hpc/notify_hpc_event.py"
if [ -f "${NOTIFY_PY}" ] && command -v python3 >/dev/null 2>&1; then
    echo "[F43REM3 Wrapper] Dispatching submission notification..."
    python3 "${NOTIFY_PY}" \
        --mode submission \
        --channel both \
        --job-name F43REM3_NATIVE \
        --job-id "${job_id}" \
        --queue entry_imfdfkmq \
        --resources "1 CPU, 8GB RAM, 30m walltime" \
        --prep-commit "${EXPECTED_PREP_SHA}" \
        --qual-commit "${EXPECTED_QUAL_SHA}" || true
fi
