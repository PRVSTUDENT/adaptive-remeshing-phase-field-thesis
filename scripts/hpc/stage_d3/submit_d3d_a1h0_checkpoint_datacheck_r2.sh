#!/bin/bash
set -euo pipefail
cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

AUTH="runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck_r2/D3D_A1H0_R2_AUTHORIZATION.json"
H0_FORTRAN="models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_uel.for"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_h.dat"

python3 - "${AUTH}" <<'PY'
import json,sys
try: a=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception as e: raise SystemExit("BLOCKED: malformed R2 authorization JSON: %s"%e)
required={
 "classification":"stage_d3d_a1h0_datacheck_r2_authorized",
 "predecessor_jobs":["1378003.mmaster02","1378004.mmaster02"],
 "predecessor_jobs_reached_abaqus":False,
 "scientific_inputs_changed":False,"deck_physics_changed":False,
 "fortran_content_changed":False,"runtime_history_changed":False,
 "active_set_changed":False,"tolerances_changed":False,
 "datacheck_r2_authorized":True,"maximum_r2_submissions":1,"r2_submissions_used":0,
 "full_hold_authorized":False,"phase_release_authorized":False,
 "continuation_authorized":False,"d3e_authorized":False,
 "automatic_retry_authorized":False}
bad=[f"{k}={a.get(k)!r} expected {v!r}" for k,v in required.items()
     if k not in a or type(a[k]) is not type(v) or a[k]!=v]
if bad: raise SystemExit("BLOCKED: R2 authorization rejected: "+"; ".join(bad))
PY

bash scripts/hpc/stage_d3/preflight_d3d_a1h0_datacheck.sh
FORTRAN_SHA="$(sha256sum "${H0_FORTRAN}" | awk '{print $1}')"
RUNTIME_SHA="$(sha256sum "${RUNTIME_H}" | awk '{print $1}')"

scripts/hpc/qsub_with_submitted_notify.sh --job-name d3d_a1h0_dc_r2 \
  --message "Final D3D-A1H0 isolated R2 datacheck; serial CPU1/16GB/00:45" -- \
  -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de -m abe \
  -v PROJECT_REVISION="$(git rev-parse HEAD)",D3D_A1H0_FORTRAN_SHA="${FORTRAN_SHA}",D3D_A1H0_RUNTIME_H_SHA="${RUNTIME_SHA}" \
  scripts/hpc/stage_d3/19_d3d_a1h0_checkpoint_datacheck_r2.pbs
