#!/bin/bash
set -euo pipefail
JOBID="${1}"
EVIDENCE_DIR="${2}"
cp -f abaqus.rpy* "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f F43REFINED_standard.inp "${EVIDENCE_DIR}/" 2>/dev/null || true
cp -f f43_remeshing_rule_config.json "${EVIDENCE_DIR}/" 2>/dev/null || true
echo "Evidence collected for F43REM1 job ${JOBID} into ${EVIDENCE_DIR}"
