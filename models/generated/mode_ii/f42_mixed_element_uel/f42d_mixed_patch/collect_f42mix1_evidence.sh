#!/bin/bash
set -euo pipefail

JOB_ID="${1}"
EVIDENCE_DIR="${2}"

cp -f F42MIX1.inp "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F42MIX1.dat "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F42MIX1.msg "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F42MIX1.sta "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F42MIX1.log "${EVIDENCE_DIR}/" 2>/dev/null || true

echo "Evidence collected for job ${JOB_ID} into ${EVIDENCE_DIR}"
