#!/bin/bash
# Guarded submission wrapper for F43PRE3_GEOM preanalysis job
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

EXPECTED_PREP_SHA="${EXPECTED_PREP_SHA:-400c8ae9d538719ffd2cd6d43c1bc5d0fd81e43f}"
EXPECTED_QUAL_SHA="${EXPECTED_QUAL_SHA:-40ff9617b40ad060ecf636030f32c18877984b6d}"
EXPECTED_INPUT_SHA="10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee"
EXPECTED_CAE_SHA="0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"
EXTERNAL_CAE_PATH="/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre3/ModeII_Geometry_Source_Abaqus2023.cae"

echo "[F43PRE3 Wrapper] Pre-flight verification..."

if [ "${F43PRE3_SUBMISSION_APPROVED:-0}" -ne 1 ]; then
    echo "FATAL ERROR: F43PRE3_GEOM submission not authorized by explicit human approval!" >&2
    exit 1
fi

MAX_SUBMISSIONS="${MAX_SUBMISSIONS:-0}"
if [ "${MAX_SUBMISSIONS}" -ne 1 ]; then
    echo "FATAL ERROR: MAX_SUBMISSIONS must equal 1! Got ${MAX_SUBMISSIONS}" >&2
    exit 1
fi

if [ "${AUTOMATIC_RETRY:-false}" = "true" ]; then
    echo "FATAL ERROR: Automatic retry is strictly prohibited!" >&2
    exit 1
fi

if [ "${REPLACEMENT_AUTHORIZED:-false}" = "true" ]; then
    echo "FATAL ERROR: Replacement submission is strictly prohibited!" >&2
    exit 1
fi

# Verify input deck SHA
ACTUAL_INPUT_SHA=$(sha256sum "${SCRIPT_DIR}/F43PRE3_GEOM.inp" | awk '{print $1}')
if [ "${ACTUAL_INPUT_SHA}" != "${EXPECTED_INPUT_SHA}" ]; then
    echo "FATAL ERROR: Input deck SHA mismatch! Expected ${EXPECTED_INPUT_SHA}, got ${ACTUAL_INPUT_SHA}" >&2
    exit 1
fi

# Verify external CAE SHA on cluster if present
if [ -f "${EXTERNAL_CAE_PATH}" ]; then
    ACTUAL_CAE_SHA=$(sha256sum "${EXTERNAL_CAE_PATH}" | awk '{print $1}')
    if [ "${ACTUAL_CAE_SHA}" != "${EXPECTED_CAE_SHA}" ]; then
        echo "FATAL ERROR: External CAE SHA mismatch! Expected ${EXPECTED_CAE_SHA}, got ${ACTUAL_CAE_SHA}" >&2
        exit 1
    fi
fi

# Verify qstat
if ! qstat_out=$(qstat -u "$USER" 2>&1); then
    echo "FATAL ERROR: qstat check failed!" >&2
    exit 1
fi

if echo "$qstat_out" | grep -q "F43PRE3_GEOM"; then
    echo "FATAL ERROR: F43PRE3_GEOM job is already running or queued in qstat!" >&2
    exit 1
fi

echo "[F43PRE3 Wrapper] All pre-flight checks passed."

if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[F43PRE3 Wrapper] DRY_RUN=1: qsub call skipped."
    exit 0
fi

job_id=$(qsub "${SCRIPT_DIR}/F43PRE3_GEOM.pbs")
echo "[F43PRE3 Wrapper] Submitted job ID: ${job_id}"
