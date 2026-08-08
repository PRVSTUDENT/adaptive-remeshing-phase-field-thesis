#!/bin/bash
# Collect lightweight HPC evidence for F43REM3_NATIVE
set -euo pipefail

JOB_ID="${1:-}"
if [ -z "${JOB_ID}" ]; then
    echo "Usage: $0 <PBS_JOB_ID>" >&2
    exit 1
fi

EVIDENCE_DIR="evidence/${JOB_ID}"
mkdir -p "${EVIDENCE_DIR}"

echo "[F43REM3 Collector] Collecting lightweight evidence for job ${JOB_ID} into ${EVIDENCE_DIR}..."

cp -f F43REM3_NATIVE.log "${EVIDENCE_DIR}/execution.log" 2>/dev/null || true
cp -f F43REM3_NATIVE_MANIFEST.json "${EVIDENCE_DIR}/F43REM3_NATIVE_MANIFEST.json" 2>/dev/null || true
cp -f F43REM3_ACCEPTANCE_CRITERIA.json "${EVIDENCE_DIR}/F43REM3_ACCEPTANCE_CRITERIA.json" 2>/dev/null || true

if [ -f "F43REM3_NATIVE.inp" ]; then
    sha256sum F43REM3_NATIVE.inp > "${EVIDENCE_DIR}/REFINED_INP_SHA256.txt"
fi

echo "[F43REM3 Collector] Evidence collection complete."
