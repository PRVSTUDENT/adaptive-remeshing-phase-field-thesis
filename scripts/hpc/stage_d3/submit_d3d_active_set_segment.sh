#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3d_active_seg"
PBS="scripts/hpc/stage_d3/15_d3d_active_set_segment.pbs"
DATACHECK_OK="runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck/D3D_DATACHECK.ok"
STATIC="runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck/D3D_STATIC_VALIDATION.json"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_d3d_active_set_segment_r1/d3_transfer_h.dat"
AUTH="runs/hpc/stage_d3/fracture_continuation_decision/D3D_ROUTE_B_PREPARATION_AUTHORIZATION.json"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

# Full segment remains blocked until committed datacheck review.
git ls-files --error-unmatch "${DATACHECK_OK}" >/dev/null
git ls-files --error-unmatch "${STATIC}" >/dev/null
git ls-files --error-unmatch "${RUNTIME_H}" >/dev/null
git ls-files --error-unmatch "${AUTH}" >/dev/null
grep -q "stage_d3d_datacheck_pass" "${DATACHECK_OK}"
grep -q "stage_d3d_static_validation_pass" "${STATIC}"
grep -q '"full_segment_submission_authorized": false' "${AUTH}" && {
  echo "ERROR: full segment submission is not authorized (Route B prep only)." >&2
  echo "Set full_segment_submission_authorized after committed datacheck review." >&2
  exit 3
}
# The check above intentionally fails while authorization remains false.
# After review, flip the authorization JSON field and re-run this submitter.

bash -n "${PBS}"
! grep -Eq "cp .*d3_transfer_table[.]inc" "${PBS}"

REVISION="$(git rev-parse HEAD)"
RUNTIME_SHA="$(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck/D3D_RUNTIME_STATE_VALIDATION.json").read_text(encoding="utf-8"))
print(data["sha256"])
PY
)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "D3D Route-B active-set segment full run; serial CPU1/16GB/02:00; one continuation segment to U2=0.0031" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}",D3D_RUNTIME_H_SHA="${RUNTIME_SHA}" \
     "${PBS}"
