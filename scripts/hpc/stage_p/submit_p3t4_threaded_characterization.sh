#!/bin/bash
# Guarded login-side staging and one-shot P3-T4 submission.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
P3T4_MAIL="${P3T4_MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${P3T4_AUTH_PATH:-${PROJECT_HOME}/runs/hpc/stage_p/p3t4_threaded_characterization/P3T4_AUTHORIZATION.json}"
PBS="${PROJECT_HOME}/scripts/hpc/stage_p/07_p3t4_threaded_characterization.pbs"
PACKAGE="${PROJECT_HOME}/models/parallelization/p3t4_threaded_characterization"
PREFLIGHT="${PROJECT_HOME}/scripts/validation/validate_p3t4_submission_preflight.py"

cd "${PROJECT_HOME}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7
PREFLIGHT_SUBMIT_ARGS=()
if [ "${P3T4_PREFLIGHT_ONLY:-0}" != "1" ]; then
  PREFLIGHT_SUBMIT_ARGS=(--require-submit)
fi
python3 "${PREFLIGHT}" --authorization "${AUTH}" "${PREFLIGHT_SUBMIT_ARGS[@]}"
test -z "$(git status --porcelain -- \
  models/parallelization/p3t4_threaded_characterization \
  scripts/hpc/stage_p/07_p3t4_threaded_characterization.pbs \
  scripts/hpc/stage_p/submit_p3t4_threaded_characterization.sh \
  scripts/postprocessing/extract_p3t4_state.py \
  scripts/postprocessing/parse_p3t4_diagnostics.py \
  scripts/validation/compare_p3t4_serial_reference.py \
  scripts/validation/validate_p3t4_threaded.py \
  scripts/validation/validate_p3t4_submission_preflight.py \
  scripts/validation/consume_p3t4_authorization.py)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/postprocessing/extract_p3t4_state.py \
  scripts/postprocessing/parse_p3t4_diagnostics.py \
  scripts/validation/compare_p3t4_serial_reference.py \
  scripts/validation/validate_p3t4_threaded.py \
  scripts/validation/validate_p3t4_submission_preflight.py \
  scripts/validation/consume_p3t4_authorization.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${P3T4_MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/p3t4_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}"
cp "${PACKAGE}/P3T4_threaded.inp" "${STAGE_ROOT}/P3T4_threaded.inp"
cp "${PACKAGE}/p3t4_instrumented.for" "${STAGE_ROOT}/p3t4_instrumented.for"
cp "${PACKAGE}/d2_transfer_table.inc" "${STAGE_ROOT}/d2_transfer_table.inc"
cp scripts/postprocessing/extract_p3t4_state.py "${STAGE_ROOT}/extract_p3t4_state.py"
cp scripts/postprocessing/parse_p3t4_diagnostics.py "${STAGE_ROOT}/parse_p3t4_diagnostics.py"
cp scripts/validation/validate_p3t4_threaded.py "${STAGE_ROOT}/validate_p3t4_threaded.py"
cp scripts/validation/compare_p3t4_serial_reference.py "${STAGE_ROOT}/compare_p3t4_serial_reference.py"
cp scripts/validation/validate_p3sb_baseline_serial.py "${STAGE_ROOT}/validate_p3sb_baseline_serial.py"
cp runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_STATE_OUTPUT.csv "${STAGE_ROOT}/P3SM0_STATE_OUTPUT.csv"
cp runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_RF_U.csv "${STAGE_ROOT}/P3SM0_RF_U.csv"
cp runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_ENERGY.csv "${STAGE_ROOT}/P3SM0_ENERGY.csv"
cp runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_INCREMENT_SEQUENCE.json "${STAGE_ROOT}/P3SM0_INCREMENT_SEQUENCE.json"

DECK_SHA="$(sha256sum "${STAGE_ROOT}/P3T4_threaded.inp" | awk '{print $1}')"
SOURCE_SHA="$(sha256sum "${STAGE_ROOT}/p3t4_instrumented.for" | awk '{print $1}')"
TRANSFER_SHA="$(sha256sum "${STAGE_ROOT}/d2_transfer_table.inc" | awk '{print $1}')"
MANIFEST="${STAGE_ROOT}/P3T4_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${DECK_SHA}" "${SOURCE_SHA}" "${TRANSFER_SHA}" <<'PY'
import json, sys
path, revision, deck, source, transfer = sys.argv[1:]
data = {
    "classification": "stage_p3t4_login_staging_complete",
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
  --stage-root "${STAGE_ROOT}" "${PREFLIGHT_SUBMIT_ARGS[@]}"

if [ "${P3T4_PREFLIGHT_ONLY:-0}" = "1" ]; then
  echo "P3-T4 preflight passed; submission intentionally skipped."
  exit 0
fi

JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name p3t4_threaded \
  --message "Stage P3-T4 bounded threaded characterization; 1 rank x 4 threads" \
  -- -q "${QUEUE}" -M "${P3T4_MAIL}" -m abe \
  -v "P3T4_STAGE_ROOT=${STAGE_ROOT},P3T4_MANIFEST=${MANIFEST},P3T4_DECK_SHA=${DECK_SHA},P3T4_SOURCE_SHA=${SOURCE_SHA},P3T4_TRANSFER_SHA=${TRANSFER_SHA},PROJECT_REVISION=${REVISION}" \
  "${PBS}")"
if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "P3-T4 submission returned invalid job ID; authorization remains unused: ${JOB_ID}" >&2
  exit 22
fi
python3 scripts/validation/consume_p3t4_authorization.py \
  --authorization "${AUTH}" --job-id "${JOB_ID}" --revision "${REVISION}"
echo "${JOB_ID}"
qstat -f "${JOB_ID}" |
  grep -E 'Job Id:|job_state =|queue =|Resource_List|Mail_Users|Mail_Points'
