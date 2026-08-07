#!/bin/bash
# Guarded Submission Wrapper for F43REM2_NATIVE
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [ "${F43REM2_NATIVE_SUBMISSION_AUTHORIZED:-0}" -ne 1 ]; then
    echo "ERROR: Execution not authorized. Set F43REM2_NATIVE_SUBMISSION_AUTHORIZED=1 upon explicit human chat authorization." >&2
    exit 1
fi

EXPECTED_PRED_ODB_SHA="85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72"
EXPECTED_SOURCE_CAE_SHA="889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff"
SOURCE_CAE_PATH="/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre2/ModeII_Geometry_Source.cae"
PRED_ODB_PATH="${SCRIPT_DIR}/evidence/1385392.mmaster02/F43PRE2_GEOM.odb"

# 1. External CAE SHA Check
if [ ! -f "${SOURCE_CAE_PATH}" ]; then
    echo "ERROR: Source CAE file missing at ${SOURCE_CAE_PATH}" >&2
    exit 1
fi
ACTUAL_CAE_SHA="$(sha256sum "${SOURCE_CAE_PATH}" | awk '{print $1}')"
if [ "${ACTUAL_CAE_SHA,,}" != "${EXPECTED_SOURCE_CAE_SHA,,}" ]; then
    echo "ERROR: Source CAE SHA256 mismatch. Expected ${EXPECTED_SOURCE_CAE_SHA}, got ${ACTUAL_CAE_SHA}" >&2
    exit 1
fi

# 2. Predecessor ODB SHA Check
if [ ! -f "${PRED_ODB_PATH}" ]; then
    echo "ERROR: Predecessor ODB missing at ${PRED_ODB_PATH}" >&2
    exit 1
fi
ACTUAL_ODB_SHA="$(sha256sum "${PRED_ODB_PATH}" | awk '{print $1}')"
if [ "${ACTUAL_ODB_SHA,,}" != "${EXPECTED_PRED_ODB_SHA,,}" ]; then
    echo "ERROR: Predecessor ODB SHA256 mismatch. Expected ${EXPECTED_PRED_ODB_SHA}, got ${ACTUAL_ODB_SHA}" >&2
    exit 1
fi

# 3. Queue Duplicate Check
if qstat -u "$USER" 2>/dev/null | grep -q "F43REM2_NATIVE"; then
    echo "ERROR: Active F43REM2_NATIVE job already present in queue." >&2
    exit 1
fi

echo "=== Submitting Guarded Job F43REM2_NATIVE ==="
export F43REM2_NATIVE_WRAPPER_AUTHORIZED=1
JOB_ID="$(qsub F43REM2_NATIVE.pbs)"
echo "Submitted PBS Job ID: ${JOB_ID}"
