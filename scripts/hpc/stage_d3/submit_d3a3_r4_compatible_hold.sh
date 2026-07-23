#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3a3_r4_compat_hold"
PBS="scripts/hpc/stage_d3/13_d3a3_r4_compatible_hold.pbs"
DATACHECK_OK="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible_datacheck/D3A3_R4_DATACHECK.ok"
POSTPYTHON_OK="runs/hpc/stage_d3/interrupted_transfer/r3_postpython_environment/D3A3_R3_POSTPYTHON.ok"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2/d3_transfer_h.dat"
D3A5_OK="runs/hpc/stage_d3/interrupted_transfer/compatibility_reprojection_d3a5/D3A5.ok"
PACKAGE_OK="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_PACKAGE_COMPATIBLE_R2.ok"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

git ls-files --error-unmatch "${DATACHECK_OK}" >/dev/null
grep -q "stage_d3a3_r4_compatible_datacheck_pass" "${DATACHECK_OK}"
git ls-files --error-unmatch "${POSTPYTHON_OK}" >/dev/null
grep -q "stage_d3a3_r3_postpython_environment_pass" "${POSTPYTHON_OK}"
git ls-files --error-unmatch "${RUNTIME_H}" >/dev/null
git ls-files --error-unmatch "${D3A5_OK}" >/dev/null
git ls-files --error-unmatch "${PACKAGE_OK}" >/dev/null
bash -n "${PBS}"
! grep -Eq "cp .*d3_transfer_table[.]inc" "${PBS}"
! grep -Eq '^[[:space:]]*"D3A3_R4_compatible_hold[.]odb"' "${PBS}"
grep -q 'D3A3_R4_ODB_LOCATION.json' "${PBS}"
grep -q 'skip-active-free-build' "${PBS}"
grep -q 'python/gcc/11.4.0/3.11.7' "${PBS}"

REVISION="$(git rev-parse HEAD)"
RUNTIME_SHA="$(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible_datacheck/D3A3_R4_RUNTIME_STATE_VALIDATION.json").read_text(encoding="utf-8"))
print(data["sha256"])
PY
)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "D3A3-R4 package_compatible_r2 hold; serial CPU1/16GB/02:00; gated by R4 datacheck + postpython; no D3D/D3E" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}",D3A3_R4_RUNTIME_H_SHA="${RUNTIME_SHA}" \
     "${PBS}"
