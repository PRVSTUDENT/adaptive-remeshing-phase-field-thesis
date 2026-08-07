#!/bin/bash
set -euo pipefail

JOB_ID="${1:-unknown}"
EVIDENCE_DIR="${2:-.}"

mkdir -p "${EVIDENCE_DIR}"

for ext in msg sta dat log rpy; do
    if [ -f "F42TRI2.${ext}" ]; then
        cp "F42TRI2.${ext}" "${EVIDENCE_DIR}/"
    fi
done

echo "Evidence collected for job ${JOB_ID} into ${EVIDENCE_DIR}"
