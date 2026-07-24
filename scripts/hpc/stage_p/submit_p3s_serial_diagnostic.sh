#!/bin/bash
# Prepare/submit exactly one P3-S job only after a separate authorization file exists.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entryq}"
MAIL="${MAIL:-pr21vyci@mailserver.tu-freiberg.de}"
AUTH="${PROJECT_HOME}/docs/decisions/P3S_EXECUTION_AUTHORIZATION.json"
PBS="scripts/hpc/stage_p/01_p3s_serial_diagnostic.pbs"

cd "${PROJECT_HOME}"
if [ ! -f "${AUTH}" ]; then
  echo "P3-S blocked: missing explicit P3S_EXECUTION_AUTHORIZATION.json" >&2
  exit 20
fi
python3 - "${AUTH}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
assert data.get("p3s_authorized") is True
assert data.get("maximum_submissions") == 1
assert data.get("submissions_used") == 0
assert data.get("p3t4_authorized") is False
PY

test -z "$(git status --porcelain -- \
  models/parallelization/minimal_externaldb_commonblock_test \
  scripts/hpc/stage_p \
  scripts/postprocessing/extract_p3s_diagnostic_state.py \
  scripts/postprocessing/parse_p3_diagnostic_log.py \
  scripts/validation/validate_p3s_serial_diagnostic.py)"
bash -n "${PBS}"
python3 -m py_compile \
  scripts/postprocessing/extract_p3s_diagnostic_state.py \
  scripts/postprocessing/parse_p3_diagnostic_log.py \
  scripts/validation/validate_p3s_serial_diagnostic.py
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${MAIL}" "${PBS}"

REVISION="$(git rev-parse HEAD)"
JOB_ID="$(qsub -q "${QUEUE}" -M "${MAIL}" -m abe \
  -v PROJECT_REVISION="${REVISION}" "${PBS}")"
echo "${JOB_ID}"
qstat -f "${JOB_ID}" |
  grep -E 'Job Id:|job_state =|queue =|Resource_List|Mail_Users|Mail_Points'
