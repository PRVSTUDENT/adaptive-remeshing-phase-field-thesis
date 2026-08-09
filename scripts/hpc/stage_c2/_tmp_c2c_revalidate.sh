#!/bin/bash
# Re-validate an already rebuilt refined deck (fast path after rebuild dry-run).
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
cd "${PROJECT_HOME}"
git pull --ff-only origin main >/dev/null
module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
PY=python3
DECK_DIR="${1:-/scratch/pr21vyci/adaptive-remeshing/prestage/c2c_dryrun_20260721T095828/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_dryrun}"
DECK="${DECK_DIR}/H0_refined_fullgen.inp"
FOR="${DECK_DIR}/H0_refined_fullgen.for"
OUT="/scratch/pr21vyci/adaptive-remeshing/runs/c2c_revalidate_$(date +%Y%m%dT%H%M%S)"
mkdir -p "${OUT}"
test -f "${DECK}" && test -f "${FOR}"
# Use current tree scripts/configs
${PY} scripts/validation/validate_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --deck "${DECK}" \
  --fortran "${FOR}" \
  --role H0_refined \
  --out-dir "${OUT}/static_validation" | tee "${OUT}/validate_stdout.log"
(cd "${DECK_DIR}" && sha256sum -c input_hashes.sha256) | tee "${OUT}/input_hash_check.txt"
echo "C2C_REVALIDATE_PASS out=${OUT}"
