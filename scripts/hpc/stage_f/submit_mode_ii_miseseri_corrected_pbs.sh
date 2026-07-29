#!/usr/bin/env bash
# Guarded submission wrapper for Stage F Job B: Corrected MISESERI PBS verification

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

PACKAGE_DIR="${REPO_ROOT}/models/generated/mode_ii/miseseri_preanalysis_corrected_pbs"
AUTH_FILE="${REPO_ROOT}/runs/hpc/stage_f/MODE_II_STAGE_F4_AUTHORIZATION_PROPOSAL.json"
PBS_SCRIPT="${SCRIPT_DIR}/06_mode_ii_miseseri_corrected_pbs.pbs"

EXPECTED_DECK_SHA="a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"

SCRATCH_DIR="/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_miseseri_pbs"

PREFLIGHT_ONLY=true
if [[ "${1:-}" == "--execute" ]]; then
    PREFLIGHT_ONLY=false
fi

echo "=== PREFLIGHT CHECK: Mode-II Corrected MISESERI PBS Verification ==="
echo "Package dir: ${PACKAGE_DIR}"
echo "Scratch dir: ${SCRATCH_DIR}"

if [[ ! -f "${PACKAGE_DIR}/ModeII_MISESERI_preanalysis.inp" ]]; then
    echo "ERROR: Input deck missing in ${PACKAGE_DIR}"
    exit 1
fi

DECK_SHA=$(sha256sum "${PACKAGE_DIR}/ModeII_MISESERI_preanalysis.inp" | awk '{print $1}')

if [[ "${DECK_SHA}" != "${EXPECTED_DECK_SHA}" ]]; then
    echo "ERROR: Deck SHA mismatch! Expected ${EXPECTED_DECK_SHA}, got ${DECK_SHA}"
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
cp "${PACKAGE_DIR}/ModeII_MISESERI_preanalysis.inp" "${SCRATCH_DIR}/"
cp "${PBS_SCRIPT}" "${SCRATCH_DIR}/"

cd "${SCRATCH_DIR}"

echo "Submitting PBS job..."
JOB_ID=$(qsub 06_mode_ii_miseseri_corrected_pbs.pbs)
echo "Submitted PBS Job ID: ${JOB_ID}"

# Consume authorization
python3 -c "import json; d=json.load(open('${AUTH_FILE}')); d['execution_authorized']=False; d['submission_approved']=False; json.dump(d, open('${AUTH_FILE}','w'), indent=2)"
echo "Consumed submission authorization in ${AUTH_FILE}"

exit 0
