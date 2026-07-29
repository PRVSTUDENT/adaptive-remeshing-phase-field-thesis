#!/usr/bin/env bash
# Guarded submission wrapper for Stage F Job A: Mode-II H2 u020 postpeak reference

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

PACKAGE_DIR="${REPO_ROOT}/models/generated/mode_ii/h2_uniform_serial_u020_postpeak"
AUTH_FILE="${REPO_ROOT}/runs/hpc/stage_f/MODE_II_STAGE_F4_AUTHORIZATION_PROPOSAL.json"
PBS_SCRIPT="${SCRIPT_DIR}/05_mode_ii_h2_u020_postpeak.pbs"

EXPECTED_DECK_SHA="fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf"
EXPECTED_FOR_SHA="49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"

SCRATCH_DIR="/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h2_u020_postpeak"

PREFLIGHT_ONLY=true
if [[ "${1:-}" == "--execute" ]]; then
    PREFLIGHT_ONLY=false
fi

echo "=== PREFLIGHT CHECK: Mode-II H2 u020 Postpeak Reference ==="
echo "Package dir: ${PACKAGE_DIR}"
echo "Scratch dir: ${SCRATCH_DIR}"

if [[ ! -f "${PACKAGE_DIR}/ModeII_H2_uniform_serial.inp" ]]; then
    echo "ERROR: Input deck missing in ${PACKAGE_DIR}"
    exit 1
fi

DECK_SHA=$(sha256sum "${PACKAGE_DIR}/ModeII_H2_uniform_serial.inp" | awk '{print $1}')
FOR_SHA=$(sha256sum "${PACKAGE_DIR}/ModeII_H2_uniform_serial.for" | awk '{print $1}')

if [[ "${DECK_SHA}" != "${EXPECTED_DECK_SHA}" ]]; then
    echo "ERROR: Deck SHA mismatch! Expected ${EXPECTED_DECK_SHA}, got ${DECK_SHA}"
    exit 1
fi

if [[ "${FOR_SHA}" != "${EXPECTED_FOR_SHA}" ]]; then
    echo "ERROR: Fortran SHA mismatch! Expected ${EXPECTED_FOR_SHA}, got ${FOR_SHA}"
    exit 1
fi

echo "Preflight check PASSED: Hashes match expected contract."

if [[ "${PREFLIGHT_ONLY}" == "true" ]]; then
    echo "Preflight mode complete. No job submitted. Pass --execute to submit if authorized."
    exit 0
fi

if [[ ! -f "${AUTH_FILE}" ]]; then
    echo "ERROR: Authorization proposal file missing: ${AUTH_FILE}"
    exit 1
fi

EXEC_AUTH=$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('execution_authorized', False)).lower())")
SUB_APPROVED=$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('submission_approved', False)).lower())")

if [[ "${EXEC_AUTH}" != "true" || "${SUB_APPROVED}" != "true" ]]; then
    echo "ERROR: Job submission NOT authorized in ${AUTH_FILE}"
    exit 1
fi

mkdir -p "${SCRATCH_DIR}"
cp "${PACKAGE_DIR}/ModeII_H2_uniform_serial.inp" "${SCRATCH_DIR}/"
cp "${PACKAGE_DIR}/ModeII_H2_uniform_serial.for" "${SCRATCH_DIR}/"
cp "${PBS_SCRIPT}" "${SCRATCH_DIR}/"

cd "${SCRATCH_DIR}"

echo "Submitting PBS job..."
JOB_ID=$(qsub 05_mode_ii_h2_u020_postpeak.pbs)
echo "Submitted PBS Job ID: ${JOB_ID}"

# Consume authorization
python3 -c "import json; d=json.load(open('${AUTH_FILE}')); d['execution_authorized']=False; d['submission_approved']=False; json.dump(d, open('${AUTH_FILE}','w'), indent=2)"
echo "Consumed submission authorization in ${AUTH_FILE}"

exit 0
