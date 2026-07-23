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

# Full segment remains blocked until explicit authorization flip after hardened-lane review.
git ls-files --error-unmatch "${DATACHECK_OK}" >/dev/null
git ls-files --error-unmatch "${STATIC}" >/dev/null
git ls-files --error-unmatch "${RUNTIME_H}" >/dev/null
git ls-files --error-unmatch "${AUTH}" >/dev/null
grep -q "stage_d3d_datacheck_pass" "${DATACHECK_OK}"
grep -q "stage_d3d_static_validation_pass" "${STATIC}"

python3 - <<'PY'
import json
import sys
from pathlib import Path

auth_path = Path(
    "runs/hpc/stage_d3/fracture_continuation_decision/D3D_ROUTE_B_PREPARATION_AUTHORIZATION.json"
)
try:
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
except Exception as exc:  # noqa: BLE001
    print("ERROR: cannot parse authorization JSON: %s" % exc, file=sys.stderr)
    sys.exit(3)

required = {
    "classification": "stage_d3d_route_b_preparation_authorized",
    "route": "B_one_d3d_active_set_segment",
    "full_segment_submission_authorized": True,
    "d3e_authorized": False,
    "automatic_second_segment": False,
    "peak_postpeak_authorized": False,
    "parameter_sweep_authorized": False,
}
errors = []
for key, expected in required.items():
    if key not in auth:
        errors.append("missing field %s" % key)
        continue
    if auth[key] is not expected and auth[key] != expected:
        # Strict: booleans must be exact True/False, not truthy strings.
        if type(auth[key]) is not type(expected) or auth[key] != expected:
            errors.append("%s=%r (required %r)" % (key, auth[key], expected))

if errors:
    print("ERROR: full segment submission authorization rejected:", file=sys.stderr)
    for e in errors:
        print("  - %s" % e, file=sys.stderr)
    print(
        "Do not flip authorization without committed hardened-lane review.",
        file=sys.stderr,
    )
    sys.exit(3)
print("authorization_guard_ok")
PY

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
