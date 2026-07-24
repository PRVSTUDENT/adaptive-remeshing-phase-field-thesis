#!/bin/bash
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
cd "${PROJECT_HOME}"
H0_FORTRAN="models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_uel.for"
R4_FORTRAN="models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2/d3_transfer_uel.for"
RUNTIME_H="${D3D_A1H0_PREFLIGHT_RUNTIME_H:-models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_h.dat}"
DECK="${D3D_A1H0_PREFLIGHT_DECK:-models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/D3D_A1H0_checkpoint_hold.inp}"
OUTPUT_DIR="${D3D_A1H0_PREFLIGHT_OUTPUT_DIR:-runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck_r2}"
mkdir -p "${OUTPUT_DIR}"

module --force purge
module load gcc/11.4.0
module load python/gcc/11.4.0/3.11.7
module load intel/2024.2.0
module load abaqus/2023
PYTHON_BIN="$(command -v python3)"
test -n "${PYTHON_BIN}" || {
  echo "Qualified Python not found" >&2
  exit 5
}
PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(".".join(map(str,sys.version_info[:3])))')"
"${PYTHON_BIN}" -c 'import sys; assert sys.version_info[:2] == (3, 11)'
echo "qualified Python found: ${PYTHON_BIN}"
echo "Python version accepted: ${PYTHON_VERSION}"

for path in "${H0_FORTRAN}" "${R4_FORTRAN}" \
  "models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/d3_transfer_h.dat" \
  "models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/D3D_A1H0_checkpoint_hold.inp"; do
  git ls-files --error-unmatch "${path}" >/dev/null
done
cmp -s "${H0_FORTRAN}" "${R4_FORTRAN}" || {
  echo "candidate/R4 Fortran differ" >&2
  exit 6
}
FORTRAN_SHA="$(sha256sum "${H0_FORTRAN}" | awk '{print $1}')"
R4_SHA="$(sha256sum "${R4_FORTRAN}" | awk '{print $1}')"
RUNTIME_SHA="$(sha256sum "${RUNTIME_H}" | awk '{print $1}')"
test "${FORTRAN_SHA}" = "${R4_SHA}"
echo "candidate/R4 Fortran identical"

"${PYTHON_BIN}" scripts/validation/validate_d3_runtime_state_file.py \
  --input "${RUNTIME_H}" \
  --out "${OUTPUT_DIR}/D3D_A1H0_R2_RUNTIME_STATE_VALIDATION.json"
"${PYTHON_BIN}" scripts/validation/validate_d3d_a1h0_deck_static.py \
  --input "${DECK}" \
  --output "${OUTPUT_DIR}/D3D_A1H0_R2_DECK_STATIC_VALIDATION.json"

"${PYTHON_BIN}" - "${OUTPUT_DIR}" "${FORTRAN_SHA}" "${R4_SHA}" "${RUNTIME_SHA}" "${PYTHON_BIN}" "${PYTHON_VERSION}" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
runtime = json.loads((out / "D3D_A1H0_R2_RUNTIME_STATE_VALIDATION.json").read_text())
deck = json.loads((out / "D3D_A1H0_R2_DECK_STATIC_VALIDATION.json").read_text())
failures = []
if not runtime.get("runtime_state_ok"):
    failures.append("runtime_state")
if runtime.get("records") != 25600 or runtime.get("duplicates") != 0 or runtime.get("missing_records") != 0:
    failures.append("runtime_state_counts")
if not deck.get("deck_static_ok"):
    failures.append("deck_static")
if deck.get("step1_fixed_phase_nodes") != 6601 or deck.get("step2_fixed_phase_nodes") != 6601:
    failures.append("fixed_phase_counts")
if deck.get("phase_release_step_present") or deck.get("continuation_step_present"):
    failures.append("prohibited_step")
status = {
    "classification": "stage_d3d_a1h0_datacheck_r2_preflight_pass" if not failures else "stage_d3d_a1h0_datacheck_r2_preflight_fail",
    "preflight_ok": not failures,
    "qualified_python": sys.argv[5],
    "python_version": sys.argv[6],
    "candidate_fortran_sha256": sys.argv[2],
    "accepted_r4_fortran_sha256": sys.argv[3],
    "fortran_byte_identical": sys.argv[2] == sys.argv[3],
    "runtime_H_sha256": sys.argv[4],
    "runtime_H_records": runtime.get("records"),
    "runtime_H_duplicates": runtime.get("duplicates"),
    "runtime_H_missing_records": runtime.get("missing_records"),
    "step1_fixed_phase_nodes": deck.get("step1_fixed_phase_nodes"),
    "step2_fixed_phase_nodes": deck.get("step2_fixed_phase_nodes"),
    "phase_release_step_present": deck.get("phase_release_step_present"),
    "continuation_step_present": deck.get("continuation_step_present"),
    "checkpoint_u2_unchanged": deck.get("checkpoint_u2_unchanged"),
    "candidate_package": deck.get("candidate_package"),
    "failures": failures,
}
(out / "D3D_A1H0_R2_PREFLIGHT_SUMMARY.json").write_text(
    json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(status, indent=2, sort_keys=True))
if failures:
    raise SystemExit(1)
PY

echo "runtime H records = 25600"
echo "duplicates = 0"
echo "missing records = 0"
echo "Step 1 fixed phase nodes = 6601"
echo "Step 2 fixed phase nodes = 6601"
echo "release step absent"
echo "continuation step absent"
echo "preflight classification = pass"
