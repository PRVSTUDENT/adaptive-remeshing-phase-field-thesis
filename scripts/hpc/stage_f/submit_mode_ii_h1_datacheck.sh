#!/usr/bin/env bash
# Submit wrapper for Stage F Mode-II H1 datacheck (defaults to preflight-only unless --submit is provided).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

SUBMIT=false
for arg in "$@"; do
  if [ "${arg}" = "--submit" ]; then
    SUBMIT=true
  fi
done

AUTH_FILE="${PROJECT_ROOT}/runs/hpc/stage_f/mode_ii_h1/MODE_II_H1_AUTHORIZATION.json"
if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: authorization file missing: ${AUTH_FILE}" >&2
  exit 1
fi

echo "Preflight check for Mode-II H1 datacheck:"
echo "  Authorization file: ${AUTH_FILE}"
echo "  Submit requested: ${SUBMIT}"
echo "  QSUB count: 0 (preflight mode active)"

if [ "${SUBMIT}" = "true" ]; then
  DATACHECK_AUTH="$(python3 -c "import json; print(str(json.load(open('${AUTH_FILE}')).get('datacheck_authorized', False)).lower())" 2>/dev/null || echo "false")"
  if [ "${DATACHECK_AUTH}" != "true" ]; then
    echo "ERROR: datacheck_authorized is false in ${AUTH_FILE}" >&2
    exit 2
  fi
  echo "Submitting H1 datacheck job..."
  # qsub command would go here upon explicit approval
fi
