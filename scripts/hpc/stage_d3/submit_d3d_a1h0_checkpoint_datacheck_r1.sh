#!/bin/bash
set -euo pipefail
cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

AUTH="runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck_r1/D3D_A1H0_R1_AUTHORIZATION.json"
H0_FORTRAN="models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_uel.for"
R4_FORTRAN="models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2/d3_transfer_uel.for"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_h.dat"

python3 - "${AUTH}" <<'PY'
import json,sys
try: a=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception as e: raise SystemExit("BLOCKED: malformed R1 authorization JSON: %s"%e)
required={
 "classification":"stage_d3d_a1h0_datacheck_r1_authorized",
 "datacheck_r1_authorized":True,"maximum_r1_submissions":1,"r1_submissions_used":0,
 "predecessor_job":"1378003.mmaster02","predecessor_authorization_consumed":True,
 "predecessor_abaqus_launched":False,"scientific_inputs_changed":False,
 "deck_changed":False,"fortran_content_changed":False,"runtime_history_changed":False,
 "tolerances_changed":False,"full_hold_authorized":False,"phase_release_authorized":False,
 "continuation_authorized":False,"d3e_authorized":False,"automatic_retry_authorized":False}
bad=[f"{k}={a.get(k)!r} expected {v!r}" for k,v in required.items()
     if k not in a or type(a[k]) is not type(v) or a[k]!=v]
if bad: raise SystemExit("BLOCKED: R1 authorization rejected: "+"; ".join(bad))
PY

for path in "${H0_FORTRAN}" "${R4_FORTRAN}" "${RUNTIME_H}"; do
  git ls-files --error-unmatch "${path}" >/dev/null 2>&1 || {
    echo "BLOCKED: required tracked file missing: ${path}" >&2
    exit 4
  }
done
cmp -s "${H0_FORTRAN}" "${R4_FORTRAN}" || {
  echo "BLOCKED: H0 and accepted-R4 Fortran differ" >&2
  exit 4
}
FORTRAN_SHA="$(sha256sum "${H0_FORTRAN}" | awk '{print $1}')"
R4_SHA="$(sha256sum "${R4_FORTRAN}" | awk '{print $1}')"
RUNTIME_SHA="$(sha256sum "${RUNTIME_H}" | awk '{print $1}')"
test -n "${FORTRAN_SHA}" && test -n "${R4_SHA}" && test -n "${RUNTIME_SHA}" || {
  echo "BLOCKED: checkout-local SHA missing" >&2
  exit 4
}
test "${FORTRAN_SHA}" = "${R4_SHA}" || {
  echo "BLOCKED: checkout-local Fortran SHA mismatch" >&2
  exit 4
}

scripts/hpc/qsub_with_submitted_notify.sh --job-name d3d_a1h0_dc_r1 \
  --message "D3D-A1H0 corrected isolated R1 datacheck; serial CPU1/16GB/00:45" -- \
  -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de -m abe \
  -v PROJECT_REVISION="$(git rev-parse HEAD)",D3D_A1H0_FORTRAN_SHA="${FORTRAN_SHA}",D3D_A1H0_RUNTIME_H_SHA="${RUNTIME_SHA}" \
  scripts/hpc/stage_d3/18_d3d_a1h0_checkpoint_datacheck_r1.pbs
