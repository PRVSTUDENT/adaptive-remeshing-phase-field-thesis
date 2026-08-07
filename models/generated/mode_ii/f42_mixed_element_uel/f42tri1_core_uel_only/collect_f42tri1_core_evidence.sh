#!/bin/bash
# Evidence Collector for F42TRI1_CORE
set -euo pipefail

JOB_ID="${1:-}"
EVIDENCE_DIR="${2:-}"

if [ -z "${JOB_ID}" ] || [ -z "${EVIDENCE_DIR}" ]; then
    echo "Usage: collect_f42tri1_core_evidence.sh <JOB_ID> <EVIDENCE_DIR>" >&2
    exit 1
fi

mkdir -p "${EVIDENCE_DIR}"

for ext in log sta dat msg; do
    if [ -f "F42TRI1_CORE.${ext}" ]; then
        cp "F42TRI1_CORE.${ext}" "${EVIDENCE_DIR}/" || true
    fi
done

qstat -x -f "${JOB_ID}" > "${EVIDENCE_DIR}/qstat_f.txt" 2>&1 || true
echo "Evidence collected successfully in ${EVIDENCE_DIR}"
