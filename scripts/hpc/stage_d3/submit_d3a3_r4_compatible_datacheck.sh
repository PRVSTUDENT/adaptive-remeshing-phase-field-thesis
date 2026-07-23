#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3a3_r4_compat_dc"
PBS="scripts/hpc/stage_d3/12_d3a3_r4_compatible_datacheck.pbs"
STATIC="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible_datacheck/D3A3_R4_STATIC_VALIDATION.json"
ACTIVE="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible_datacheck/D3A3_R4_ACTIVE_SET_BOUNDARY_AUDIT.json"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2/d3_transfer_h.dat"
D3A5_OK="runs/hpc/stage_d3/interrupted_transfer/compatibility_reprojection_d3a5/D3A5.ok"
PACKAGE_OK="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_PACKAGE_COMPATIBLE_R2.ok"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

git ls-files --error-unmatch "${D3A5_OK}" >/dev/null
git ls-files --error-unmatch "${PACKAGE_OK}" >/dev/null
git ls-files --error-unmatch "${RUNTIME_H}" >/dev/null
git ls-files --error-unmatch "${STATIC}" >/dev/null
git ls-files --error-unmatch "${ACTIVE}" >/dev/null
grep -q "stage_d3a3_r4_static_validation_pass" "${STATIC}"
grep -q '"step3_active_boundary_exact": true' "${ACTIVE}"
grep -q '"step3_free_node_phase_bc_count": 0' "${ACTIVE}"
grep -q '"active_nodes": 6446' "${ACTIVE}"
grep -q '"free_nodes": 155' "${ACTIVE}"
bash -n "${PBS}"
! grep -Eq "cp .*d3_transfer_table[.]inc" "${PBS}"

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
  --message "D3A3-R4 package_compatible_r2 datacheck; serial CPU1/16GB/00:45; active 6446 free 155; no full analysis" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}",D3A3_R4_RUNTIME_H_SHA="${RUNTIME_SHA}" \
     "${PBS}"
