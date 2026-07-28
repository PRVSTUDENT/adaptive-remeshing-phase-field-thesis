#!/bin/bash
# Stage F Mode-II H0 endpoint-corrected serial solver submission wrapper.
# Guarded submission wrapper: defaults to preflight only; requires explicit authorization file and environment flag.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AUTH_FILE="${AUTH_FILE:-${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json}"
PBS_SCRIPT="${ROOT_DIR}/scripts/hpc/stage_f/04_mode_ii_h0_endpoint_corrected_serial.pbs"
PACKAGE_DIR="${ROOT_DIR}/models/generated/mode_ii/h0_endpoint_corrected_serial"
DATACHECK_EVIDENCE_DIR="${ROOT_DIR}/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/evidence/1379387.mmaster02"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"

EXPECTED_DECK_SHA="c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef"
EXPECTED_SOURCE_SHA="5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"
EXPECTED_PREP_REVISION="f7e44ae6e7df7dcf1b7eb468eaa946b2eec9caae"
EXPECTED_DATACHECK_JOB="1379387.mmaster02"
EXPECTED_DATACHECK_CLOSEOUT_REV="91d6fad0b972687380759c30a3a268515a733339"

echo "Mode-II H0 Endpoint-Corrected Serial Solver Wrapper (Guarded)"

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

EXTRACTOR_SRC="${ROOT_DIR}/scripts/postprocessing/extract_molnar_single_notch.py"
VALIDATOR_SRC="${ROOT_DIR}/scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py"
STUDY_CFG_SRC="${ROOT_DIR}/configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"

if [ ! -f "${EXTRACTOR_SRC}" ] || [ ! -f "${VALIDATOR_SRC}" ] || [ ! -f "${STUDY_CFG_SRC}" ]; then
  echo "ERROR: Required runtime scripts or configs missing locally."
  exit 1
fi

# Determine current project revision
REVISION="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || echo "unknown")"
if [ -z "${REVISION}" ] || [ "${REVISION}" = "unknown" ]; then
  echo "ERROR: Could not resolve git HEAD revision."
  exit 1
fi

# Preflight authorization checks via Python helper
PREFLIGHT_JSON="$(python3 - "${AUTH_FILE}" "${REVISION}" <<'PY'
import json, sys
try:
    auth_file, current_rev = sys.argv[1], sys.argv[2]
    d = json.load(open(auth_file, encoding="utf-8"))
    res = {
        "classification": d.get("classification", ""),
        "solver_authorized": d.get("solver_authorized", False),
        "solver_submissions_used": d.get("solver_submissions_used", 1),
        "maximum_solver_submissions": d.get("maximum_solver_submissions", 1),
        "submission_approved": d.get("submission_approved", False),
        "execution_authorized": d.get("execution_authorized", False),
        "automatic_retry_authorized": d.get("automatic_retry_authorized", False),
        "retry_authorized": d.get("retry_authorized", False),
        "mpi_authorized": d.get("mpi_authorized", False),
        "threaded_execution_authorized": d.get("threaded_execution_authorized", False),
        "hybrid_authorized": d.get("hybrid_authorized", False),
        "h1_authorized": d.get("h1_authorized", False),
        "maximum_jobs_now": d.get("maximum_jobs_now", 0),
        "approved_project_revision": d.get("approved_project_revision", ""),
        "solver_contract_preparation_revision": d.get("solver_contract_preparation_revision", ""),
        "datacheck_job_id": d.get("datacheck_job_id", ""),
        "datacheck_closeout_revision": d.get("datacheck_closeout_revision", ""),
        "datacheck_result_status": d.get("datacheck_result_status", "")
    }
    print(json.dumps(res))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PY
)"

CLASSIFICATION="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('classification', ''))" 2>/dev/null || echo "")"
SOLVER_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('solver_authorized', False)).lower())" 2>/dev/null || echo "false")"
SOLVER_USED="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('solver_submissions_used', 1))" 2>/dev/null || echo "1")"
MAX_SOLVER_SUB="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('maximum_solver_submissions', 1))" 2>/dev/null || echo "1")"
SUBMISSION_APPROVED="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('submission_approved', False)).lower())" 2>/dev/null || echo "false")"
EXECUTION_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('execution_authorized', False)).lower())" 2>/dev/null || echo "false")"
AUTO_RETRY_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('automatic_retry_authorized', False)).lower())" 2>/dev/null || echo "false")"
RETRY_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('retry_authorized', False)).lower())" 2>/dev/null || echo "false")"
MPI_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('mpi_authorized', False)).lower())" 2>/dev/null || echo "false")"
THREAD_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('threaded_execution_authorized', False)).lower())" 2>/dev/null || echo "false")"
HYBRID_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('hybrid_authorized', False)).lower())" 2>/dev/null || echo "false")"
H1_AUTH="$(python3 -c "import json; print(str(json.loads('''${PREFLIGHT_JSON}''').get('h1_authorized', False)).lower())" 2>/dev/null || echo "false")"
MAX_JOBS="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('maximum_jobs_now', 0))" 2>/dev/null || echo "0")"

APPROVED_REV="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('approved_project_revision', ''))" 2>/dev/null || echo "")"
PREP_REV="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('solver_contract_preparation_revision', ''))" 2>/dev/null || echo "")"
DC_JOB="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('datacheck_job_id', ''))" 2>/dev/null || echo "")"
DC_CLOSEOUT_REV="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('datacheck_closeout_revision', ''))" 2>/dev/null || echo "")"
DC_STATUS="$(python3 -c "import json; print(json.loads('''${PREFLIGHT_JSON}''').get('datacheck_result_status', ''))" 2>/dev/null || echo "")"

ALLOW_SUBMIT="${ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT:-0}"

# Hash verification of local package
LOCAL_DECK_SHA="$(sha256sum "${PACKAGE_DIR}/ModeII_H0_endpoint_corrected_serial.inp" | awk '{print $1}')"
LOCAL_SOURCE_SHA="$(sha256sum "${PACKAGE_DIR}/ModeII_H0_endpoint_corrected_serial.for" | awk '{print $1}')"

if [ "${LOCAL_DECK_SHA}" != "${EXPECTED_DECK_SHA}" ] || [ "${LOCAL_SOURCE_SHA}" != "${EXPECTED_SOURCE_SHA}" ]; then
  echo "ERROR: Package hash mismatch."
  echo "Deck SHA: ${LOCAL_DECK_SHA} (expected ${EXPECTED_DECK_SHA})"
  echo "Source SHA: ${LOCAL_SOURCE_SHA} (expected ${EXPECTED_SOURCE_SHA})"
  exit 1
fi

if [ "${AUTO_RETRY_AUTH}" = "true" ] || [ "${RETRY_AUTH}" = "true" ] || [ "${MPI_AUTH}" = "true" ] || [ "${THREAD_AUTH}" = "true" ] || [ "${HYBRID_AUTH}" = "true" ] || [ "${H1_AUTH}" = "true" ]; then
  echo "ERROR: Prohibited execution modes authorized in auth JSON (retry/mpi/threaded/hybrid/h1 must be false)."
  exit 1
fi

REQUIRED_CLASSIFICATION="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved"

if [ "${CLASSIFICATION}" != "${REQUIRED_CLASSIFICATION}" ] || \
   [ "${SOLVER_AUTH}" != "true" ] || \
   [ "${SOLVER_USED}" -ge "${MAX_SOLVER_SUB}" ] || \
   [ "${SUBMISSION_APPROVED}" != "true" ] || \
   [ "${EXECUTION_AUTH}" != "true" ] || \
   [ "${ALLOW_SUBMIT}" != "1" ] || \
   [ "${MAX_JOBS}" -ne 1 ] || \
   [ "${APPROVED_REV}" != "${REVISION}" ] || \
   [ "${PREP_REV}" != "${EXPECTED_PREP_REVISION}" ] || \
   [ "${DC_JOB}" != "${EXPECTED_DATACHECK_JOB}" ] || \
   [ "${DC_CLOSEOUT_REV}" != "${EXPECTED_DATACHECK_CLOSEOUT_REV}" ] || \
   [ "${DC_STATUS}" != "pass" ]; then
  echo "Preflight check PASS (Submission NOT authorized)."
  echo "classification: ${CLASSIFICATION}"
  echo "solver_authorized: ${SOLVER_AUTH}"
  echo "solver_submissions_used: ${SOLVER_USED}"
  echo "submission_approved: ${SUBMISSION_APPROVED}"
  echo "execution_authorized: ${EXECUTION_AUTH}"
  echo "maximum_jobs_now: ${MAX_JOBS}"
  echo "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT: ${ALLOW_SUBMIT}"
  echo "approved_project_revision: ${APPROVED_REV} (current: ${REVISION})"
  echo "solver_contract_preparation_revision: ${PREP_REV}"
  echo "datacheck_job_id: ${DC_JOB}"
  echo "datacheck_closeout_revision: ${DC_CLOSEOUT_REV}"
  echo "datacheck_result_status: ${DC_STATUS}"
  exit 0
fi

# Tracked clean repository check (excluding the authorization file itself)
AUTH_REL="$(python3 -c "import os; print(os.path.relpath('${AUTH_FILE}', '${ROOT_DIR}'))" 2>/dev/null || echo "")"
DIRTY_TRACKED="$(git -C "${ROOT_DIR}" status --porcelain --untracked-files=no | grep -v "${AUTH_REL}" | grep -v "^.. runs/hpc/" || true)"
if [ -n "${DIRTY_TRACKED}" ]; then
  echo "ERROR: Tracked repository files are dirty."
  echo "${DIRTY_TRACKED}"
  exit 1
fi

# Verify committed datacheck evidence
DC_STATUS_FILE="${DATACHECK_EVIDENCE_DIR}/MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_STATUS.json"
DC_HASH_FILE="${DATACHECK_EVIDENCE_DIR}/input_hash_check.txt"

if [ ! -f "${DC_STATUS_FILE}" ] || [ ! -f "${DC_HASH_FILE}" ]; then
  echo "ERROR: Committed datacheck evidence missing in ${DATACHECK_EVIDENCE_DIR}"
  exit 1
fi

DC_EVIDENCE_VALID="$(python3 - "${DC_STATUS_FILE}" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    ok = d.get("DATACHECK_ok", False) is True
    rc = d.get("abaqus_return_code", -1) == 0
    cls = d.get("classification", "") == "stage_f_mode_ii_h0_endpoint_corrected_datacheck_pass"
    print("true" if (ok and rc and cls) else "false")
except Exception:
    print("false")
PY
)"

if [ "${DC_EVIDENCE_VALID}" != "true" ]; then
  echo "ERROR: Committed datacheck status evidence is invalid or not passed."
  exit 1
fi

if ! grep -q "ModeII_H0_endpoint_corrected_serial.inp: OK" "${DC_HASH_FILE}" || ! grep -q "ModeII_H0_endpoint_corrected_serial.for: OK" "${DC_HASH_FILE}"; then
  echo "ERROR: Datacheck evidence input_hash_check.txt missing OK for inp/for files."
  exit 1
fi

# Duplicate job check on scheduler if qstat is available
if command -v qstat >/dev/null 2>&1; then
  EXISTING="$(qstat -u "${USER:-pr21vyci}" 2>/dev/null | grep "mode_ii_h0_endpoint_corrected_serial" || true)"
  if [ -n "${EXISTING}" ]; then
    echo "ERROR: Existing serial solver job already queued or running on cluster."
    echo "${EXISTING}"
    exit 1
  fi
fi

EXTRACTOR_SHA="$(sha256sum "${EXTRACTOR_SRC}" | awk '{print $1}')"
VALIDATOR_SHA="$(sha256sum "${VALIDATOR_SRC}" | awk '{print $1}')"
CONFIG_SHA="$(sha256sum "${STUDY_CFG_SRC}" | awk '{print $1}')"

# Create login-side prestaged root
STAGE_ROOT="${SCRATCH_ROOT:-/scratch/pr21vyci/adaptive-remeshing}/mode_ii_h0_endpoint_corrected_staged/${REVISION}"
RUNTIME_ROOT="${STAGE_ROOT}/runtime"
STAGED_PKG_DIR="${STAGE_ROOT}/models/generated/mode_ii/h0_endpoint_corrected_serial"

mkdir -p "${STAGE_ROOT}/models/generated/mode_ii"
mkdir -p "${RUNTIME_ROOT}/scripts/postprocessing"
mkdir -p "${RUNTIME_ROOT}/scripts/validation"
mkdir -p "${RUNTIME_ROOT}/configs/studies"

rm -rf "${STAGED_PKG_DIR}"
cp -a "${PACKAGE_DIR}" "${STAGED_PKG_DIR}"
printf '%s\n' "${REVISION}" > "${STAGE_ROOT}/PROJECT_REVISION.txt"

cp "${EXTRACTOR_SRC}" "${RUNTIME_ROOT}/scripts/postprocessing/extract_molnar_single_notch.py"
cp "${VALIDATOR_SRC}" "${RUNTIME_ROOT}/scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py"
cp "${STUDY_CFG_SRC}" "${RUNTIME_ROOT}/configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"
if [ -f "${ROOT_DIR}/scripts/validation/__init__.py" ]; then
  cp "${ROOT_DIR}/scripts/validation/__init__.py" "${RUNTIME_ROOT}/scripts/validation/__init__.py"
fi

STAGED_DECK="${STAGED_PKG_DIR}/ModeII_H0_endpoint_corrected_serial.inp"
STAGED_SOURCE="${STAGED_PKG_DIR}/ModeII_H0_endpoint_corrected_serial.for"

if [ ! -f "${STAGED_DECK}" ] || [ ! -f "${STAGED_SOURCE}" ]; then
  echo "ERROR: Staged package files missing in ${STAGE_ROOT}"
  exit 1
fi

STAGED_DECK_SHA="$(sha256sum "${STAGED_DECK}" | awk '{print $1}')"
STAGED_SOURCE_SHA="$(sha256sum "${STAGED_SOURCE}" | awk '{print $1}')"

if [ "${STAGED_DECK_SHA}" != "${EXPECTED_DECK_SHA}" ] || [ "${STAGED_SOURCE_SHA}" != "${EXPECTED_SOURCE_SHA}" ]; then
  echo "ERROR: Staged package hash mismatch."
  exit 1
fi

MANIFEST="${STAGE_ROOT}/MODE_II_H0_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${CLASSIFICATION}" "${AUTH_FILE}" "${APPROVED_REV}" "${PREP_REV}" "${DC_JOB}" "${DC_CLOSEOUT_REV}" "${STAGED_PKG_DIR}" "${STAGED_DECK_SHA}" "${STAGED_SOURCE_SHA}" "${RUNTIME_ROOT}" "${EXTRACTOR_SHA}" "${VALIDATOR_SHA}" "${CONFIG_SHA}" "${QUEUE}" <<'PY'
import json, sys
(
    path, revision, auth_cls, auth_path, approved_rev, prep_rev, dc_job, dc_closeout_rev,
    pkg_dir, deck_sha, source_sha, runtime_root, ext_sha, val_sha, cfg_sha, queue
) = sys.argv[1:]

data = {
    "classification": "stage_f_mode_ii_h0_endpoint_corrected_serial_solver_login_staging_complete",
    "project_revision": revision,
    "authorization_classification": auth_cls,
    "authorization_path": auth_path,
    "approved_project_revision": approved_rev,
    "solver_contract_preparation_revision": prep_rev,
    "datacheck_job_id": dc_job,
    "datacheck_closeout_revision": dc_closeout_rev,
    "package_path": pkg_dir,
    "deck_sha256": deck_sha,
    "source_sha256": source_sha,
    "runtime_root": runtime_root,
    "extractor_path": "scripts/postprocessing/extract_molnar_single_notch.py",
    "extractor_sha256": ext_sha,
    "validator_path": "scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py",
    "validator_sha256": val_sha,
    "configuration_path": "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml",
    "configuration_sha256": cfg_sha,
    "cpus": 1,
    "mpi_ranks": 1,
    "omp_threads": 1,
    "memory": "16 GB",
    "walltime": "04:00:00",
    "queue": queue,
    "compute_git_required": False
}

json.dump(data, open(path, "w", encoding="utf-8"), indent=2, sort_keys=True)
open(path, "a", encoding="utf-8").write("\n")
PY

echo "Executing guarded serial solver submission..."
echo "PRESTAGED_ROOT=${STAGE_ROOT}"
echo "LOGIN_MANIFEST_PATH=${MANIFEST}"
echo "PROJECT_REVISION=${REVISION}"
echo "PRESTAGED_RUNTIME_ROOT=${RUNTIME_ROOT}"

QSUB_HELPER="${QSUB_HELPER:-${ROOT_DIR}/scripts/hpc/qsub_with_submitted_notify.sh}"
if [ ! -f "${QSUB_HELPER}" ]; then
  QSUB_HELPER="qsub"
fi

JOB_ID="$("${QSUB_HELPER}" \
  --job-name mode_ii_h0_endpoint_corrected_serial \
  --message "Stage F1-C2-R1 Mode-II H0 endpoint-corrected serial solver; 1 rank x 1 thread; one-shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "PRESTAGED_ROOT=${STAGE_ROOT},LOGIN_MANIFEST_PATH=${MANIFEST},PROJECT_REVISION=${REVISION},PRESTAGED_RUNTIME_ROOT=${RUNTIME_ROOT}" \
  "${PBS_SCRIPT}")"

if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "ERROR: Serial solver qsub returned invalid job ID: ${JOB_ID}" >&2
  exit 22
fi

echo "Submitted serial solver PBS Job ID: ${JOB_ID}"
