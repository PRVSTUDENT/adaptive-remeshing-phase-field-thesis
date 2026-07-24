#!/bin/bash
set -euo pipefail
cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
AUTH="runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_decision/D3D_A1H0_AUTHORIZATION.json"
python3 - "${AUTH}" <<'PY'
import json, sys
auth = json.load(open(sys.argv[1], encoding="utf-8"))
if auth.get("datacheck_authorized") is not True:
    raise SystemExit("BLOCKED: D3D-A1H0 datacheck is not authorized")
PY
scripts/hpc/qsub_with_submitted_notify.sh --job-name d3d_a1h0_dc \
  --message "D3D-A1H0 fixed-phase checkpoint datacheck" -- \
  -v PROJECT_REVISION="$(git rev-parse HEAD)" \
  scripts/hpc/stage_d3/16_d3d_a1h0_checkpoint_datacheck.pbs
