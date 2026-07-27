#!/bin/bash
# Stage F Mode-II H0 endpoint-corrected datacheck submission wrapper.
# Guarded submission wrapper: defaults to preflight only; requires explicit authorization file and environment flag.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AUTH_FILE="${AUTH_FILE:-${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json}"
if [ ! -f "${AUTH_FILE}" ]; then
  AUTH_FILE="${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json"
fi

PBS_SCRIPT="${ROOT_DIR}/scripts/hpc/stage_f/03_mode_ii_h0_endpoint_corrected_datacheck.pbs"
PACKAGE_DIR="${ROOT_DIR}/models/generated/mode_ii/h0_endpoint_corrected_serial"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"

EXPECTED_DECK_SHA="c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef"
EXPECTED_SOURCE_SHA="5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"

echo "Mode-II H0 Endpoint-Corrected Datacheck Wrapper (Guarded)"

if [ ! -f "${AUTH_FILE}" ]; then
  echo "ERROR: Authorization file missing: ${AUTH_FILE}"
  exit 1
fi

if [ ! -d "${PACKAGE_DIR}" ]; then
  echo "ERROR: Package directory missing: ${PACKAGE_DIR}"
  exit 1
fi

if [ ! -f "${PBS_SCRIPT}" ]; then
  echo "ERROR: PBS script missing: ${PBS_SCRIPT}"
  exit 1
fi

# Preflight authorization checks via Python helper
PREFLIGHT_JSON="$(python3 - "${AUTH_FILE}" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    res = {
        "datacheck_authorized": d.get("datacheck_authorized", False),
        "datacheck_submissions_used": d.get("datacheck_submissions_used", 1),
        "submission_approved": d.get("submission_approved", False),
        "solver_authorized": d.get("solver_authorized", False),
        "automatic_retry_authorized": d.get("automatic_retry_authorized", False),
        "mpi_authorized": d.get("mpi_authorized", False),
        "threaded_execution_authorized": d.get("threaded_execution_authorized", False),
        "hybrid_authorized": d.get("hybrid_authorized", False),
        "maximum_jobs_now": d.get("maximum_jobs_now", 0)
    }
    print(json.dumps(res))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PY
)"

DATACHECK_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('datacheck_authorized', False)).lower())" 2>/dev/null || echo "false")"
DATACHECK_USED="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('datacheck_submissions_used', 1))" 2>/dev/null || echo "1")"
SUBMISSION_APPROVED="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('submission_approved', False)).lower())" 2>/dev/null || echo "false")"
SOLVER_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('solver_authorized', False)).lower())" 2>/dev/null || echo "false")"
RETRY_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('automatic_retry_authorized', False)).lower())" 2>/dev/null || echo "false")"
MPI_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('mpi_authorized', False)).lower())" 2>/dev/null || echo "false")"
THREAD_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('threaded_execution_authorized', False)).lower())" 2>/dev/null || echo "false")"
MAX_JOBS="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('maximum_jobs_now', 0))" 2>/dev/null || echo "0")"

ALLOW_SUBMIT="${ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT:-0}"

# Hash verification of local package
LOCAL_DECK_SHA="$(sha256sum "${PACKAGE_DIR}/ModeII_H0_endpoint_corrected_serial.inp" | awk '{print $1}')"
LOCAL_SOURCE_SHA="$(sha256sum "${PACKAGE_DIR}/ModeII_H0_endpoint_corrected_serial.for" | awk '{print $1}')"

if [ "${LOCAL_DECK_SHA}" != "${EXPECTED_DECK_SHA}" ] || [ "${LOCAL_SOURCE_SHA}" != "${EXPECTED_SOURCE_SHA}" ]; then
  echo "ERROR: Package hash mismatch."
  echo "Deck SHA: ${LOCAL_DECK_SHA} (expected ${EXPECTED_DECK_SHA})"
  echo "Source SHA: ${LOCAL_SOURCE_SHA} (expected ${EXPECTED_SOURCE_SHA})"
  exit 1
fi

if [ "${SOLVER_AUTH}" = "true" ] || [ "${RETRY_AUTH}" = "true" ] || [ "${MPI_AUTH}" = "true" ] || [ "${THREAD_AUTH}" = "true" ]; then
  echo "ERROR: Prohibited execution modes authorized in auth JSON (solver/retry/mpi/threaded must be false)."
  exit 1
fi

if [ "${DATACHECK_AUTH}" != "true" ] || [ "${DATACHECK_USED}" -ge 1 ] || [ "${SUBMISSION_APPROVED}" != "true" ] || [ "${ALLOW_SUBMIT}" != "1" ] || [ "${MAX_JOBS}" -lt 1 ]; then
  echo "Preflight check PASS (Submission NOT authorized)."
  echo "datacheck_authorized: ${DATACHECK_AUTH}"
  echo "datacheck_submissions_used: ${DATACHECK_USED}"
  echo "submission_approved: ${SUBMISSION_APPROVED}"
  echo "maximum_jobs_now: ${MAX_JOBS}"
  echo "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT: ${ALLOW_SUBMIT}"
  exit 0
fi

# Duplicate job check on scheduler if qstat is available
if command -v qstat >/dev/null 2>&1; then
  EXISTING="$(qstat -u "${USER:-pr21vyci}" 2>/dev/null | grep "mode_ii_h0_endpoint_corrected_datacheck" || true)"
  if [ -n "${EXISTING}" ]; then
    echo "ERROR: Existing datacheck job already queued or running on cluster."
    echo "${EXISTING}"
    exit 1
  fi
fi

# Determine project revision
REVISION="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || echo "unknown")"
if [ -z "${REVISION}" ] || [ "${REVISION}" = "unknown" ]; then
  echo "ERROR: Could not resolve git HEAD revision."
  exit 1
fi

# Create login-side prestaged root
STAGE_ROOT="${SCRATCH_ROOT:-/scratch/pr21vyci/adaptive-remeshing}/mode_ii_h0_endpoint_corrected_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}/models/generated/mode_ii"
rm -rf "${STAGE_ROOT}/models/generated/mode_ii/h0_endpoint_corrected_serial"
cp -a "${PACKAGE_DIR}" "${STAGE_ROOT}/models/generated/mode_ii/h0_endpoint_corrected_serial"
printf '%s\n' "${REVISION}" > "${STAGE_ROOT}/PROJECT_REVISION.txt"

STAGED_DECK="${STAGE_ROOT}/models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"
STAGED_SOURCE="${STAGE_ROOT}/models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.for"

if [ ! -f "${STAGED_DECK}" ] || [ ! -f "${STAGED_SOURCE}" ]; then
  echo "ERROR: Staged files missing in ${STAGE_ROOT}"
  exit 1
fi

STAGED_DECK_SHA="$(sha256sum "${STAGED_DECK}" | awk '{print $1}')"
STAGED_SOURCE_SHA="$(sha256sum "${STAGED_SOURCE}" | awk '{print $1}')"

if [ "${STAGED_DECK_SHA}" != "${EXPECTED_DECK_SHA}" ] || [ "${STAGED_SOURCE_SHA}" != "${EXPECTED_SOURCE_SHA}" ]; then
  echo "ERROR: Staged package hash mismatch."
  exit 1
fi

MANIFEST="${STAGE_ROOT}/MODE_II_H0_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${STAGED_DECK_SHA}" "${STAGED_SOURCE_SHA}" <<'PY'
import json, sys
path, revision, deck, source = sys.argv[1:]
json.dump(
    {
        "classification": "stage_f_mode_ii_h0_endpoint_corrected_login_staging_complete",
        "project_revision": revision,
        "deck_sha256": deck,
        "source_sha256": source,
        "compute_git_required": False,
    },
    open(path, "w", encoding="utf-8"),
    indent=2,
    sort_keys=True,
)
open(path, "a", encoding="utf-8").write("\n")
PY

echo "Executing guarded datacheck submission..."
echo "PRESTAGED_ROOT=${STAGE_ROOT}"
echo "LOGIN_MANIFEST_PATH=${MANIFEST}"
echo "PROJECT_REVISION=${REVISION}"

QSUB_HELPER="${QSUB_HELPER:-${ROOT_DIR}/scripts/hpc/qsub_with_submitted_notify.sh}"
if [ ! -f "${QSUB_HELPER}" ]; then
  QSUB_HELPER="qsub"
fi

JOB_ID="$("${QSUB_HELPER}" \
  --job-name mode_ii_h0_endpoint_corrected_datacheck \
  --message "Stage F1-C2-R1 Mode-II H0 endpoint-corrected datacheck; 1 rank x 1 thread; one-shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "PRESTAGED_ROOT=${STAGE_ROOT},LOGIN_MANIFEST_PATH=${MANIFEST},PROJECT_REVISION=${REVISION}" \
  "${PBS_SCRIPT}")"

if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "ERROR: Datacheck qsub returned invalid job ID: ${JOB_ID}" >&2
  exit 22
fi

echo "Submitted datacheck PBS Job ID: ${JOB_ID}"
