#!/bin/bash
# Guarded login-side staging and one-shot Mode-II H0 datacheck submission.
# Default is preflight-only unless MODE_II_H0_SUBMIT=1 and authorization is true.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${MODE_II_H0_AUTH_PATH:-${PROJECT_HOME}/runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json}"
PBS="${PROJECT_HOME}/scripts/hpc/stage_f/01_mode_ii_h0_datacheck.pbs"
PACKAGE="${PROJECT_HOME}/models/generated/mode_ii/h0_serial"
PREFLIGHT="${PROJECT_HOME}/scripts/validation/validate_mode_ii_h0_submission_preflight.py"

cd "${PROJECT_HOME}"
module purge >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7

python3 scripts/validation/validate_mode_ii_h0_static.py --package "${PACKAGE}"
python3 "${PREFLIGHT}" --authorization "${AUTH}" --package "${PACKAGE}"

if [ "${MODE_II_H0_SUBMIT:-0}" != "1" ]; then
  echo "Mode-II H0 datacheck preparation/preflight only; submission not requested."
  echo "Set MODE_II_H0_SUBMIT=1 after a separate authorization-only commit."
  exit 0
fi

python3 "${PREFLIGHT}" --authorization "${AUTH}" --package "${PACKAGE}" --require-datacheck
test -z "$(git status --porcelain -- \
  models/generated/mode_ii/h0_serial \
  scripts/hpc/stage_f/01_mode_ii_h0_datacheck.pbs \
  scripts/hpc/stage_f/submit_mode_ii_h0_datacheck.sh \
  scripts/validation/validate_mode_ii_h0_static.py \
  scripts/validation/validate_mode_ii_h0_submission_preflight.py \
  scripts/validation/consume_mode_ii_h0_authorization.py \
  runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/validation/validate_mode_ii_h0_static.py \
  scripts/validation/validate_mode_ii_h0_submission_preflight.py \
  scripts/validation/consume_mode_ii_h0_authorization.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_staged/${REVISION}"
mkdir -p "${STAGE_ROOT}/models/generated/mode_ii"
rm -rf "${STAGE_ROOT}/models/generated/mode_ii/h0_serial"
cp -a "${PACKAGE}" "${STAGE_ROOT}/models/generated/mode_ii/h0_serial"
printf '%s\n' "${REVISION}" > "${STAGE_ROOT}/PROJECT_REVISION.txt"

DECK_SHA="$(sha256sum "${STAGE_ROOT}/models/generated/mode_ii/h0_serial/ModeII_H0_serial.inp" | awk '{print $1}')"
SOURCE_SHA="$(sha256sum "${STAGE_ROOT}/models/generated/mode_ii/h0_serial/ModeII_H0_serial.for" | awk '{print $1}')"
MANIFEST="${STAGE_ROOT}/MODE_II_H0_LOGIN_MANIFEST.json"
python3 - "${MANIFEST}" "${REVISION}" "${DECK_SHA}" "${SOURCE_SHA}" <<'PY'
import json, sys
path, revision, deck, source = sys.argv[1:]
json.dump(
    {
        "classification": "stage_f_mode_ii_h0_login_staging_complete",
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

JOB_ID="$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name mode_ii_h0_dc \
  --message "Stage F1-J0 Mode-II H0 datacheck; 1 rank x 1 thread; one-shot" \
  -- -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v "PRESTAGED_ROOT=${STAGE_ROOT},PROJECT_REVISION=${REVISION}" \
  "${PBS}")"
if [[ ! "${JOB_ID}" =~ ^[0-9]+([.][A-Za-z0-9_-]+)?$ ]]; then
  echo "Mode-II H0 datacheck qsub returned invalid job ID; authorization unused: ${JOB_ID}" >&2
  exit 22
fi
python3 scripts/validation/consume_mode_ii_h0_authorization.py \
  --authorization "${AUTH}" --job-id "${JOB_ID}" --revision "${REVISION}" --kind datacheck
echo "${JOB_ID}"
