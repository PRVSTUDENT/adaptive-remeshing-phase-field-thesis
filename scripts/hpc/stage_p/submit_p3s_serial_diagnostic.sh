#!/bin/bash
# Login-node preparation and guarded submission for exactly one P3-S job.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entryq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${P3S_AUTH_PATH:-${PROJECT_HOME}/runs/hpc/stage_p/p3s_serial_diagnostic/P3S_AUTHORIZATION.json}"
PBS="${PROJECT_HOME}/scripts/hpc/stage_p/01_p3s_serial_diagnostic.pbs"
PACKAGE="${PROJECT_HOME}/models/parallelization/minimal_externaldb_commonblock_test"
PREFLIGHT="${PROJECT_HOME}/scripts/validation/validate_p3s_submission_preflight.py"

cd "${PROJECT_HOME}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7

# This exits nonzero for missing, malformed, false, or consumed authorization.
python3 "${PREFLIGHT}" --authorization "${AUTH}" --require-submit

test -z "$(git status --porcelain -- \
  models/parallelization/minimal_externaldb_commonblock_test \
  scripts/hpc/stage_p \
  scripts/postprocessing/extract_p3s_diagnostic_state.py \
  scripts/postprocessing/parse_p3_diagnostic_log.py \
  scripts/validation/validate_p3s_serial_diagnostic.py \
  scripts/validation/validate_p3s_submission_preflight.py)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/postprocessing/extract_p3s_diagnostic_state.py \
  scripts/postprocessing/parse_p3_diagnostic_log.py \
  scripts/validation/validate_p3s_serial_diagnostic.py \
  scripts/validation/validate_p3s_submission_preflight.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/p3s_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}"

stage_file() {
  local source="$1"
  local target="$2"
  test -f "${source}"
  cp "${source}" "${target}"
}

stage_file "${PACKAGE}/P3S_serial_diagnostic.inp" "${STAGE_ROOT}/P3S_serial_diagnostic.inp"
stage_file "${PACKAGE}/p2_instrumented_commonblock.for" "${STAGE_ROOT}/p3_instrumented_commonblock.for"
stage_file "${PACKAGE}/d2_transfer_table.inc" "${STAGE_ROOT}/d2_transfer_table.inc"
stage_file "scripts/postprocessing/extract_p3s_diagnostic_state.py" "${STAGE_ROOT}/extract_p3s_diagnostic_state.py"
stage_file "scripts/postprocessing/parse_p3_diagnostic_log.py" "${STAGE_ROOT}/parse_p3_diagnostic_log.py"
stage_file "scripts/validation/validate_p3s_serial_diagnostic.py" "${STAGE_ROOT}/validate_p3s_serial_diagnostic.py"

DECK_SHA="$(sha256sum "${STAGE_ROOT}/P3S_serial_diagnostic.inp" | awk '{print $1}')"
SOURCE_SHA="$(sha256sum "${STAGE_ROOT}/p3_instrumented_commonblock.for" | awk '{print $1}')"
TRANSFER_SHA="$(sha256sum "${STAGE_ROOT}/d2_transfer_table.inc" | awk '{print $1}')"
test -n "${DECK_SHA}" && test -n "${SOURCE_SHA}" && test -n "${TRANSFER_SHA}"

MANIFEST="${STAGE_ROOT}/P3S_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${DECK_SHA}" "${SOURCE_SHA}" "${TRANSFER_SHA}" <<'PY'
import json, sys
path, revision, deck_sha, source_sha, transfer_sha = sys.argv[1:]
data = {
    "classification": "stage_p3_serial_login_staging_complete",
    "project_revision": revision,
    "deck_sha256": deck_sha,
    "source_sha256": source_sha,
    "transfer_sha256": transfer_sha,
    "compute_git_required": False,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
python3 "${PREFLIGHT}" --authorization "${AUTH}" --manifest "${MANIFEST}" \
  --stage-root "${STAGE_ROOT}" --require-submit

if [ "${P3S_PREFLIGHT_ONLY:-0}" = "1" ]; then
  echo "P3-S login preflight passed; qsub intentionally skipped."
  exit 0
fi

JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name p3s_serial \
  --message "Stage P3-S serial diagnostic; 1 rank x 1 thread; one-shot authorization" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "P3S_STAGE_ROOT=${STAGE_ROOT},P3S_MANIFEST=${MANIFEST},P3S_DECK_SHA=${DECK_SHA},P3S_SOURCE_SHA=${SOURCE_SHA},P3S_TRANSFER_SHA=${TRANSFER_SHA},PROJECT_REVISION=${REVISION}" \
  "${PBS}")"
echo "${JOB_ID}"
qstat -f "${JOB_ID}" |
  grep -E 'Job Id:|job_state =|queue =|Resource_List|Mail_Users|Mail_Points'
