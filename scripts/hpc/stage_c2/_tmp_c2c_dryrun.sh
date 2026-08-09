#!/bin/bash
# One-shot C2C dry-run against frozen C2B products (login node).
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
C2B="/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/C2B_REFINED_MESH"
STAMP="$(date +%Y%m%dT%H%M%S)"
DRY="/scratch/pr21vyci/adaptive-remeshing/runs/c2c_dryrun_${STAMP}"
PRESTAGE="/scratch/pr21vyci/adaptive-remeshing/prestage/c2c_dryrun_${STAMP}"
cd "${PROJECT_HOME}"
REV="$(git rev-parse HEAD)"
echo "revision=${REV}"
echo "C2B=${C2B}"
test -f "${C2B}/C2B_FIELD_SUMMARY.json"
test -f "${C2B}/refined_mesh_nodes.csv"
test -f "${C2B}/refined_mesh_elements.csv"
test -f models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp
test -f models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for
mkdir -p "${PRESTAGE}" "${DRY}"
REQUIRED_PATHS=(
  "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension"
  "models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact"
  "models/generated/molnar_gravouil_2017/unified_preprocessing"
  "configs/preprocessing/molnar_h0_h1_unified.yaml"
  "configs/remeshing/miseseri_h0_to_h1_initial.json"
  "configs/studies/molnar_lc015_h_convergence.yaml"
  "results/processed/molnar_lc015_h_convergence"
  "scripts/preprocessing"
  "scripts/postprocessing"
  "scripts/validation"
  "scripts/remeshing"
  "scripts/model_generation"
  "scripts/hpc/stage_c2"
)
git archive "${REV}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGE}"
test -f "${PRESTAGE}/models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
test -f "${PRESTAGE}/models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"
echo "baseline_ok"
module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
PY=python3
echo "using_python=$(command -v ${PY}) $(${PY} --version 2>&1)"
${PY} -c "import yaml; print('yaml_import_ok')"
${PY} - <<PY
import json
from pathlib import Path
report = json.loads(Path("${C2B}/C2B_FIELD_SUMMARY.json").read_text())
cls = report.get("classification") or report.get("scientific_classification")
assert cls == "miseseri_preanalysis_suitable_for_remeshing", cls
assert report.get("gate_pass") is not False
man = json.loads(Path("${C2B}/remeshing_rule_manifest.json").read_text())
assert man.get("status") == "pass", man
print("c2b_verified", cls, "n_elements=", man.get("n_elements"))
PY
OUT="${PRESTAGE}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_dryrun"
mkdir -p "${OUT}"
cd "${PRESTAGE}"
echo "=== rebuild start ==="
${PY} scripts/preprocessing/build_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --role-name H0_refined \
  --output-profile fracture_baseline \
  --from-nodes-csv "${C2B}/refined_mesh_nodes.csv" \
  --from-elems-csv "${C2B}/refined_mesh_elements.csv" \
  --out "${OUT}" > "${DRY}/rebuild_stdout.log" 2>&1
echo "rebuild_exit=$?"
ls -la "${OUT}" | head -40
tail -30 "${DRY}/rebuild_stdout.log"
DECK="$(ls ${OUT}/*fullgen.inp ${OUT}/*.inp 2>/dev/null | head -n1)"
FOR="$(ls ${OUT}/*fullgen.for ${OUT}/*.for 2>/dev/null | head -n1)"
echo "DECK=${DECK}"
echo "FOR=${FOR}"
test -n "${DECK}" && test -f "${DECK}"
test -n "${FOR}" && test -f "${FOR}"
echo "=== validate start ==="
${PY} scripts/validation/validate_molnar_unified_deck.py \
  --deck "${DECK}" \
  --fortran "${FOR}" \
  --role H0_refined \
  --out-dir "${DRY}/static_validation" > "${DRY}/validate_stdout.log" 2>&1
echo "validate_exit=$?"
tail -50 "${DRY}/validate_stdout.log"
if [ -f "${OUT}/input_hashes.sha256" ]; then
  (cd "${OUT}" && sha256sum -c input_hashes.sha256) > "${DRY}/input_hash_check.txt" 2>&1 || {
    echo "hash_check_failed"
    cat "${DRY}/input_hash_check.txt"
    exit 12
  }
  cat "${DRY}/input_hash_check.txt"
fi
echo "DRY_DIR=${DRY}"
echo "PRESTAGE=${PRESTAGE}"
echo "C2C_DRYRUN_PASS"
