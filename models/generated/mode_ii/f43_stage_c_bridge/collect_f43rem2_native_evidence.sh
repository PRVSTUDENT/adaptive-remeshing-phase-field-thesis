#!/bin/bash
# Evidence Collector for F43REM2_NATIVE
set -euo pipefail

JOB_ID="${1:-}"
EVIDENCE_DIR="${2:-}"

if [ -z "${JOB_ID}" ] || [ -z "${EVIDENCE_DIR}" ]; then
    echo "Usage: bash collect_f43rem2_native_evidence.sh <JOB_ID> <EVIDENCE_DIR>" >&2
    exit 1
fi

mkdir -p "${EVIDENCE_DIR}"

qstat -f "${JOB_ID}" > "${EVIDENCE_DIR}/QSTAT_FINAL.txt" 2>&1 || true
tracejob "${JOB_ID}" > "${EVIDENCE_DIR}/TRACEJOB.txt" 2>&1 || true

# Copy lightweight outputs
for ext in inp json log txt rpy; do
    cp -f *.${ext} "${EVIDENCE_DIR}/" 2>/dev/null || true
done

echo "Evidence collected cleanly for job ${JOB_ID} in ${EVIDENCE_DIR}"
