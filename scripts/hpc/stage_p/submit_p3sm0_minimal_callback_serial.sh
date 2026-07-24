#!/bin/bash
# Guarded login-side staging and one-shot P3-SM0 submission.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${P3SM0_AUTH_PATH:-${PROJECT_HOME}/runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_AUTHORIZATION.json}"
PBS="${PROJECT_HOME}/scripts/hpc/stage_p/03_p3sm0_minimal_callback_serial.pbs"
PACKAGE="${PROJECT_HOME}/models/parallelization/p3sm0_minimal_callback_serial"
PREFLIGHT="${PROJECT_HOME}/scripts/validation/validate_p3sm0_submission_preflight.py"

cd "${PROJECT_HOME}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7
python3 "${PREFLIGHT}" --authorization "${AUTH}" --require-submit
test -z "$(git status --porcelain -- \
  models/parallelization/p3sm0_minimal_callback_serial \
  scripts/hpc/stage_p/03_p3sm0_minimal_callback_serial.pbs \
  scripts/hpc/stage_p/submit_p3sm0_minimal_callback_serial.sh \
  scripts/postprocessing/extract_p3sm0_state.py \
  scripts/postprocessing/parse_p3sm0_callback_log.py \
  scripts/validation/validate_p3sm0_serial.py \
  scripts/validation/validate_p3sm0_submission_preflight.py \
  scripts/validation/consume_p3sm0_authorization.py)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/postprocessing/extract_p3sm0_state.py \
  scripts/postprocessing/parse_p3sm0_callback_log.py \
  scripts/validation/validate_p3sm0_serial.py \
  scripts/validation/validate_p3sm0_submission_preflight.py \
  scripts/validation/consume_p3sm0_authorization.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/p3sm0_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}"
cp "${PACKAGE}/P3SM0_serial.inp" "${STAGE_ROOT}/P3SM0_serial.inp"
cp "${PACKAGE}/p3sm0_minimal_callback.for" "${STAGE_ROOT}/p3sm0_minimal_callback.for"
cp "${PACKAGE}/d2_transfer_table.inc" "${STAGE_ROOT}/d2_transfer_table.inc"
cp scripts/postprocessing/extract_p3sm0_state.py "${STAGE_ROOT}/extract_p3sm0_state.py"
cp scripts/postprocessing/parse_p3sm0_callback_log.py "${STAGE_ROOT}/parse_p3sm0_callback_log.py"
cp scripts/validation/validate_p3sm0_serial.py "${STAGE_ROOT}/validate_p3sm0_serial.py"
cp scripts/validation/validate_p3sb_baseline_serial.py "${STAGE_ROOT}/validate_p3sb_baseline_serial.py"

DECK_SHA="$(sha256sum "${STAGE_ROOT}/P3SM0_serial.inp" | awk '{print $1}')"
SOURCE_SHA="$(sha256sum "${STAGE_ROOT}/p3sm0_minimal_callback.for" | awk '{print $1}')"
TRANSFER_SHA="$(sha256sum "${STAGE_ROOT}/d2_transfer_table.inc" | awk '{print $1}')"
MANIFEST="${STAGE_ROOT}/P3SM0_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${DECK_SHA}" "${SOURCE_SHA}" "${TRANSFER_SHA}" <<'PY'
import json, sys
path, revision, deck, source, transfer = sys.argv[1:]
data = {
    "classification": "stage_p3sm0_login_staging_complete",
    "project_revision": revision,
    "deck_sha256": deck,
    "source_sha256": source,
    "transfer_sha256": transfer,
    "compute_git_required": False,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
python3 "${PREFLIGHT}" --authorization "${AUTH}" --manifest "${MANIFEST}" \
  --stage-root "${STAGE_ROOT}" --require-submit

if [ "${P3SM0_PREFLIGHT_ONLY:-0}" = "1" ]; then
  echo "P3-SM0 preflight passed; submission intentionally skipped."
  exit 0
fi

JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name p3sm0_serial \
  --message "Stage P3-SM0 minimal callback serial; 1 rank x 1 thread; one shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "P3SM0_STAGE_ROOT=${STAGE_ROOT},P3SM0_MANIFEST=${MANIFEST},P3SM0_DECK_SHA=${DECK_SHA},P3SM0_SOURCE_SHA=${SOURCE_SHA},P3SM0_TRANSFER_SHA=${TRANSFER_SHA},PROJECT_REVISION=${REVISION}" \
  "${PBS}")"
if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "P3-SM0 submission returned invalid job ID; authorization remains unused: ${JOB_ID}" >&2
  exit 22
fi
python3 scripts/validation/consume_p3sm0_authorization.py \
  --authorization "${AUTH}" --job-id "${JOB_ID}" --revision "${REVISION}"
echo "${JOB_ID}"
qstat -f "${JOB_ID}" |
  grep -E 'Job Id:|job_state =|queue =|Resource_List|Mail_Users|Mail_Points'
