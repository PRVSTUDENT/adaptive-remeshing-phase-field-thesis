#!/bin/bash
set -euo pipefail

JOB_ID="${1}"
EVIDENCE_DIR="${2}"

cp -f F43PRE2_GEOM.inp "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F43PRE2_GEOM.dat "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F43PRE2_GEOM.msg "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F43PRE2_GEOM.sta "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F43PRE2_GEOM.log "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F43PRE2_GEOM.odb "${EVIDENCE_DIR}/" 2>/dev/null || true

echo "Evidence collected for job ${JOB_ID} into ${EVIDENCE_DIR}"
