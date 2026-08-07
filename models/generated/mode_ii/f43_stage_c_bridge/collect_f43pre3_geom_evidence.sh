#!/bin/bash
# Collect lightweight HPC evidence for F43PRE3_GEOM
set -euo pipefail

JOB_ID="${1:-}"
if [ -z "${JOB_ID}" ]; then
    echo "Usage: $0 <PBS_JOB_ID>" >&2
    exit 1
fi

EVIDENCE_DIR="evidence/${JOB_ID}"
mkdir -p "${EVIDENCE_DIR}"

echo "[F43PRE3 Collector] Collecting lightweight evidence for job ${JOB_ID} into ${EVIDENCE_DIR}..."

cp -f F43PRE3_GEOM.log "${EVIDENCE_DIR}/execution.log" 2>/dev/null || true
cp -f F43PRE3_GEOM.sta "${EVIDENCE_DIR}/F43PRE3_GEOM.sta" 2>/dev/null || true
cp -f F43PRE3_GEOM.msg "${EVIDENCE_DIR}/F43PRE3_GEOM.msg" 2>/dev/null || true
cp -f F43PRE3_GEOM.dat "${EVIDENCE_DIR}/F43PRE3_GEOM.dat" 2>/dev/null || true
cp -f F43PRE3_SOURCE_MANIFEST.json "${EVIDENCE_DIR}/F43PRE3_SOURCE_MANIFEST.json" 2>/dev/null || true
cp -f F43PRE3_ACCEPTANCE_CRITERIA.json "${EVIDENCE_DIR}/F43PRE3_ACCEPTANCE_CRITERIA.json" 2>/dev/null || true

if [ -f "F43PRE3_GEOM.odb" ]; then
    sha256sum F43PRE3_GEOM.odb > "${EVIDENCE_DIR}/ODB_SHA256.txt"
fi

echo "[F43PRE3 Collector] Evidence collection complete."
