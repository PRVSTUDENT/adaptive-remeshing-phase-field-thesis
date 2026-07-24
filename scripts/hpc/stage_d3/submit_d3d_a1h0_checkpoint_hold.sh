#!/bin/bash
set -euo pipefail
cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
AUTH="runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_decision/D3D_A1H0_AUTHORIZATION.json"
DC_OK="runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck/D3D_A1H0_DATACHECK.ok"
git ls-files --error-unmatch "${DC_OK}" >/dev/null 2>&1 || { echo "BLOCKED: committed passing datacheck marker required" >&2; exit 3; }
grep -q stage_d3d_a1h0_datacheck_pass "${DC_OK}" || { echo "BLOCKED: datacheck marker invalid" >&2; exit 3; }
python3 - "${AUTH}" <<'PY'
import json,sys
try: a=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception as e: raise SystemExit("BLOCKED: malformed authorization JSON: %s"%e)
required={"classification":"stage_d3d_a1h0_mechanical_hold_preparation_authorized","preparation_authorized":True,"solver_submission_authorized":True,"phase_release_authorized":False,"continuation_authorized":False,"d3e_authorized":False,"automatic_retry":False,"tolerance_change":False}
bad=[f"{k}={a.get(k)!r} expected {v!r}" for k,v in required.items() if k not in a or type(a[k]) is not type(v) or a[k]!=v]
if bad: raise SystemExit("BLOCKED: full-hold authorization rejected: "+"; ".join(bad))
PY
scripts/hpc/qsub_with_submitted_notify.sh --job-name d3d_a1h0_hold \
  --message "D3D-A1H0 fixed-phase mechanical checkpoint hold" -- \
  -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de -m abe \
  -v PROJECT_REVISION="$(git rev-parse HEAD)" \
  scripts/hpc/stage_d3/17_d3d_a1h0_checkpoint_hold.pbs
