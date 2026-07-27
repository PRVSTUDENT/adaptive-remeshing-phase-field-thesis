#!/bin/bash
# Guarded login-side staging and one-shot Mode-II H0 serial solver submission.
# Default is preflight-only unless MODE_II_H0_SOLVER_SUBMIT=1 and authorization is true.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${MODE_II_H0_AUTH_PATH:-${PROJECT_HOME}/runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json}"
PBS="${PROJECT_HOME}/scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs"
PACKAGE="${PROJECT_HOME}/models/generated/mode_ii/h0_serial"
PREFLIGHT="${PROJECT_HOME}/scripts/validation/validate_mode_ii_h0_submission_preflight.py"

cd "${PROJECT_HOME}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 || {
  echo "ERROR: module load python/gcc/11.4.0/3.11.7 failed" >&2
  exit 5
}
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'

python3 scripts/validation/validate_mode_ii_h0_static.py --package "${PACKAGE}"
python3 "${PREFLIGHT}" --authorization "${AUTH}" --package "${PACKAGE}"

if [ "${MODE_II_H0_SOLVER_SUBMIT:-0}" != "1" ]; then
  echo "Mode-II H0 serial solver preparation/preflight only; submission not requested."
  echo "Set MODE_II_H0_SOLVER_SUBMIT=1 after a separate solver authorization commit."
  exit 0
fi

python3 "${PREFLIGHT}" --authorization "${AUTH}" --package "${PACKAGE}" --require-solver
test -z "$(git status --porcelain -- \
  models/generated/mode_ii/h0_serial \
  scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs \
  scripts/hpc/stage_f/submit_mode_ii_h0_serial.sh \
  scripts/postprocessing/extract_molnar_single_notch.py \
  scripts/validation/validate_mode_ii_h0_static.py \
  scripts/validation/validate_mode_ii_h0_submission_preflight.py \
  scripts/validation/validate_mode_ii_h0_serial_results.py \
  scripts/validation/verify_mode_ii_h0_runtime_staging.py \
  scripts/validation/consume_mode_ii_h0_authorization.py \
  runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/validation/validate_mode_ii_h0_static.py \
  scripts/validation/validate_mode_ii_h0_submission_preflight.py \
  scripts/validation/consume_mode_ii_h0_authorization.py \
  scripts/postprocessing/extract_molnar_single_notch.py \
  scripts/validation/validate_mode_ii_h0_serial_results.py \
  scripts/validation/verify_mode_ii_h0_runtime_staging.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}/models/generated/mode_ii"
mkdir -p "${STAGE_ROOT}/runtime/scripts/hpc/stage_f"
mkdir -p "${STAGE_ROOT}/runtime/scripts/postprocessing"
mkdir -p "${STAGE_ROOT}/runtime/scripts/validation"

rm -rf "${STAGE_ROOT}/models/generated/mode_ii/h0_serial"
cp -a "${PACKAGE}" "${STAGE_ROOT}/models/generated/mode_ii/h0_serial"
cp -a "${PBS}" "${STAGE_ROOT}/runtime/scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs"
cp -a scripts/postprocessing/extract_molnar_single_notch.py "${STAGE_ROOT}/runtime/scripts/postprocessing/"
cp -a scripts/validation/validate_mode_ii_h0_serial_results.py "${STAGE_ROOT}/runtime/scripts/validation/"
cp -a scripts/validation/verify_mode_ii_h0_runtime_staging.py "${STAGE_ROOT}/runtime/scripts/validation/"
printf '%s\n' "${REVISION}" > "${STAGE_ROOT}/PROJECT_REVISION.txt"

STAGED_PBS="${STAGE_ROOT}/runtime/scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs"

DECK_SHA="$(sha256sum "${STAGE_ROOT}/models/generated/mode_ii/h0_serial/ModeII_H0_serial.inp" | awk '{print $1}')"
SOURCE_SHA="$(sha256sum "${STAGE_ROOT}/models/generated/mode_ii/h0_serial/ModeII_H0_serial.for" | awk '{print $1}')"
EXTRACTOR_SHA="$(sha256sum "${STAGE_ROOT}/runtime/scripts/postprocessing/extract_molnar_single_notch.py" | awk '{print $1}')"
VALIDATOR_SHA="$(sha256sum "${STAGE_ROOT}/runtime/scripts/validation/validate_mode_ii_h0_serial_results.py" | awk '{print $1}')"
STAGING_CHECKER_SHA="$(sha256sum "${STAGE_ROOT}/runtime/scripts/validation/verify_mode_ii_h0_runtime_staging.py" | awk '{print $1}')"
PBS_SHA="$(sha256sum "${STAGED_PBS}" | awk '{print $1}')"

LOGIN_MANIFEST="${STAGE_ROOT}/MODE_II_H0_LOGIN_MANIFEST.json"
python3 - "${LOGIN_MANIFEST}" "${REVISION}" "${DECK_SHA}" "${SOURCE_SHA}" "${EXTRACTOR_SHA}" "${VALIDATOR_SHA}" "${STAGING_CHECKER_SHA}" "${PBS_SHA}" <<'PY'
import json, sys
path, revision, deck, source, extractor, validator, staging_checker, pbs = sys.argv[1:]
json.dump(
    {
        "classification": "stage_f_mode_ii_h0_login_staging_complete",
        "project_revision": revision,
        "deck_sha256": deck,
        "source_sha256": source,
        "extractor_sha256": extractor,
        "validator_sha256": validator,
        "staging_checker_sha256": staging_checker,
        "pbs_script_sha256": pbs,
        "compute_git_required": False,
    },
    open(path, "w", encoding="utf-8"),
    indent=2,
    sort_keys=True,
)

open(path, "a", encoding="utf-8").write("\n")
PY

JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name mode_ii_h0_serial \
  --message "Stage F1-J1 Mode-II H0 serial solver; 1 rank x 1 thread; one-shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "PRESTAGED_ROOT=${STAGE_ROOT},PRESTAGED_RUNTIME_ROOT=${STAGE_ROOT}/runtime,LOGIN_MANIFEST_PATH=${LOGIN_MANIFEST},PROJECT_REVISION=${REVISION}" \
  "${STAGED_PBS}")"
if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "Mode-II H0 serial solver qsub returned invalid job ID; authorization unused: ${JOB_ID}" >&2
  exit 22
fi
python3 scripts/validation/consume_mode_ii_h0_authorization.py \
  --authorization "${AUTH}" --job-id "${JOB_ID}" --revision "${REVISION}" --kind solver
echo "${JOB_ID}"
