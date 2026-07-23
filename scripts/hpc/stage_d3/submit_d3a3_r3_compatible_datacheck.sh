#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3a3_r3_compat_dc"
PBS="scripts/hpc/stage_d3/08_d3a3_r3_compatible_datacheck.pbs"
STATIC="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible_datacheck/D3A3_R3_STATIC_VALIDATION.json"
ACTIVE="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible_datacheck/D3A3_R3_ACTIVE_SET_BOUNDARY_AUDIT.json"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

git ls-files --error-unmatch "runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4/D3A4.ok" >/dev/null
git ls-files --error-unmatch "runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/D3_PACKAGE_COMPATIBLE_R1.ok" >/dev/null
git ls-files --error-unmatch "models/state_transfer/d3_interrupted_transfer/executable_r3_compatible/d3_transfer_h.dat" >/dev/null
git ls-files --error-unmatch "${STATIC}" >/dev/null
grep -q "stage_d3a3_r3_static_validation_pass" "${STATIC}"
grep -q '"step3_active_boundary_exact": true' "${ACTIVE}"
grep -q '"step3_free_node_phase_bc_count": 0' "${ACTIVE}"
bash -n "${PBS}"
! grep -Eq "cp .*d3_transfer_table[.]inc" "${PBS}"

REVISION="$(git rev-parse HEAD)"
RUNTIME_SHA="$(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible_datacheck/D3A3_R3_RUNTIME_STATE_VALIDATION.json").read_text(encoding="utf-8"))
print(data["sha256"])
PY
)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "D3A3-R3 compatible active-set datacheck; serial CPU1/16GB/00:45; Step3 active phase BC only" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}",D3A3_R3_RUNTIME_H_SHA="${RUNTIME_SHA}" \
     "${PBS}"
