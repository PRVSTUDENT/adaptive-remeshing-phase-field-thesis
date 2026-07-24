#!/bin/bash
set -euo pipefail
cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
AUTH="runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_decision/D3D_A1H0_AUTHORIZATION.json"
python3 - "${AUTH}" <<'PY'
import json,sys
try: a=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception as e: raise SystemExit("BLOCKED: malformed authorization JSON: %s"%e)
required={"classification":"stage_d3d_a1h0_mechanical_hold_preparation_authorized","preparation_authorized":True,"datacheck_authorized":True,"datacheck_authorization_classification":"stage_d3d_a1h0_datacheck_authorized","maximum_datacheck_submissions":1,"datacheck_submissions_used":0,"solver_submission_authorized":False,"phase_release_authorized":False,"continuation_authorized":False,"d3e_authorized":False,"automatic_retry":False,"tolerance_change":False}
bad=[f"{k}={a.get(k)!r} expected {v!r}" for k,v in required.items() if k not in a or type(a[k]) is not type(v) or a[k]!=v]
if bad: raise SystemExit("BLOCKED: datacheck authorization rejected: "+"; ".join(bad))
PY
RUNTIME_SHA="$(sha256sum models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_h.dat | awk '{print $1}')"
scripts/hpc/qsub_with_submitted_notify.sh --job-name d3d_a1h0_dc \
  --message "D3D-A1H0 fixed-phase checkpoint datacheck; serial CPU1/16GB/00:45" -- \
  -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de -m abe \
  -v PROJECT_REVISION="$(git rev-parse HEAD)",D3D_A1H0_RUNTIME_H_SHA="${RUNTIME_SHA}" \
  scripts/hpc/stage_d3/16_d3d_a1h0_checkpoint_datacheck.pbs
