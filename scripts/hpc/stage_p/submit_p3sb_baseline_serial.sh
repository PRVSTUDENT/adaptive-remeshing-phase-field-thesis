#!/bin/bash
# Login-node immutable staging and guarded one-shot P3-SB submission.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${P3SB_AUTH_PATH:-${PROJECT_HOME}/runs/hpc/stage_p/p3sb_baseline_serial/P3SB_AUTHORIZATION.json}"
PBS="${PROJECT_HOME}/scripts/hpc/stage_p/02_p3sb_baseline_serial.pbs"
PACKAGE="${PROJECT_HOME}/models/parallelization/p3sb_baseline_eight_element_serial"
PREFLIGHT="${PROJECT_HOME}/scripts/validation/validate_p3sb_submission_preflight.py"

cd "${PROJECT_HOME}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7

python3 "${PREFLIGHT}" --authorization "${AUTH}" --require-submit
test -z "$(git status --porcelain -- \
  models/parallelization/p3sb_baseline_eight_element_serial \
  scripts/hpc/stage_p/02_p3sb_baseline_serial.pbs \
  scripts/hpc/stage_p/submit_p3sb_baseline_serial.sh \
  scripts/postprocessing/extract_p3sb_baseline_state.py \
  scripts/validation/validate_p3sb_baseline_serial.py \
  scripts/validation/validate_p3sb_submission_preflight.py \
  scripts/validation/consume_p3sb_authorization.py)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/postprocessing/extract_p3sb_baseline_state.py \
  scripts/validation/validate_p3sb_baseline_serial.py \
  scripts/validation/validate_p3sb_submission_preflight.py \
  scripts/validation/consume_p3sb_authorization.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/p3sb_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}"
cp "${PACKAGE}/P3SB_baseline_serial.inp" "${STAGE_ROOT}/P3SB_baseline_serial.inp"
cp "${PACKAGE}/p3sb_baseline_uel.for" "${STAGE_ROOT}/p3sb_baseline_uel.for"
cp "${PACKAGE}/d2_transfer_table.inc" "${STAGE_ROOT}/d2_transfer_table.inc"
cp "scripts/postprocessing/extract_p3sb_baseline_state.py" "${STAGE_ROOT}/extract_p3sb_baseline_state.py"
cp "scripts/validation/validate_p3sb_baseline_serial.py" "${STAGE_ROOT}/validate_p3sb_baseline_serial.py"

DECK_SHA="$(sha256sum "${STAGE_ROOT}/P3SB_baseline_serial.inp" | awk '{print $1}')"
SOURCE_SHA="$(sha256sum "${STAGE_ROOT}/p3sb_baseline_uel.for" | awk '{print $1}')"
TRANSFER_SHA="$(sha256sum "${STAGE_ROOT}/d2_transfer_table.inc" | awk '{print $1}')"
MANIFEST="${STAGE_ROOT}/P3SB_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${DECK_SHA}" "${SOURCE_SHA}" "${TRANSFER_SHA}" <<'PY'
import json, sys
path, revision, deck, source, transfer = sys.argv[1:]
data = {
    "classification": "stage_p3sb_login_staging_complete",
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

if [ "${P3SB_PREFLIGHT_ONLY:-0}" = "1" ]; then
  echo "P3-SB login preflight passed; submission intentionally skipped."
  exit 0
fi

JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name p3sb_baseline \
  --message "Stage P3-SB uninstrumented serial baseline; 1 rank x 1 thread; one shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "P3SB_STAGE_ROOT=${STAGE_ROOT},P3SB_MANIFEST=${MANIFEST},P3SB_DECK_SHA=${DECK_SHA},P3SB_SOURCE_SHA=${SOURCE_SHA},P3SB_TRANSFER_SHA=${TRANSFER_SHA},PROJECT_REVISION=${REVISION}" \
  "${PBS}")"
if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "P3-SB submission returned invalid job ID; authorization remains unused: ${JOB_ID}" >&2
  exit 22
fi
python3 scripts/validation/consume_p3sb_authorization.py \
  --authorization "${AUTH}" --job-id "${JOB_ID}" --revision "${REVISION}"
echo "${JOB_ID}"
qstat -f "${JOB_ID}" |
  grep -E 'Job Id:|job_state =|queue =|Resource_List|Mail_Users|Mail_Points'
