#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3d_active_seg_dc"
PBS="scripts/hpc/stage_d3/14_d3d_active_set_segment_datacheck.pbs"
STATIC="runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck/D3D_STATIC_VALIDATION.json"
ACTIVE="runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck/D3D_ACTIVE_SET_BOUNDARY_AUDIT.json"
PREP_OK="runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck/D3D_PREPARATION.ok"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_d3d_active_set_segment_r1/d3_transfer_h.dat"
AUTH="runs/hpc/stage_d3/fracture_continuation_decision/D3D_ROUTE_B_PREPARATION_AUTHORIZATION.json"
D3A3_OK="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3.ok"
PACKAGE_OK="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_PACKAGE_COMPATIBLE_R2.ok"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

git ls-files --error-unmatch "${AUTH}" >/dev/null
git ls-files --error-unmatch "${D3A3_OK}" >/dev/null
git ls-files --error-unmatch "${PACKAGE_OK}" >/dev/null
git ls-files --error-unmatch "${RUNTIME_H}" >/dev/null
git ls-files --error-unmatch "${STATIC}" >/dev/null
git ls-files --error-unmatch "${ACTIVE}" >/dev/null
git ls-files --error-unmatch "${PREP_OK}" >/dev/null
grep -q "stage_d3d_static_validation_pass" "${STATIC}"
grep -q "stage_d3d_static_validation_pass" "${PREP_OK}"
grep -q "stage_d3d_route_b_preparation_authorized" "${AUTH}"
grep -q '"step4_active_boundary_exact": true' "${ACTIVE}"
grep -q '"step4_free_node_phase_bc_count": 0' "${ACTIVE}"
grep -q '"active_nodes": 6446' "${ACTIVE}"
grep -q '"free_nodes": 155' "${ACTIVE}"
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
  --message "D3D Route-B active-set segment datacheck; serial CPU1/16GB/00:45; no solver increments" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}",D3D_RUNTIME_H_SHA="${RUNTIME_SHA}" \
     "${PBS}"
