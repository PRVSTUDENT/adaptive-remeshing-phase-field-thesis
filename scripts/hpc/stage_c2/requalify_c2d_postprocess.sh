#!/bin/bash
# Re-run C2D RF–U qualification ONLY (no Abaqus re-solve).
# Uses existing ODB from job 1376411.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
C2D_RUN="/scratch/pr21vyci/adaptive-remeshing/runs/molnar_h0_threads4_qualification_1376411.mmaster02"
ODB="${C2D_RUN}/molnar_h0_threads4_qualification.odb"
REF_CSV="${PROJECT_HOME}/results/processed/molnar_lc015_h_convergence/source_csv/H0_RF2_U2.csv"
CHAIN_STATE_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/chain_state"
OUT_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/recovery/c2d_requalification"
LIGHT_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/molnar_h0_threads4_qualification/evidence/1376411.mmaster02"

cd "${PROJECT_HOME}"
test -f "${ODB}"
test -f "${REF_CSV}"
mkdir -p "${OUT_DIR}" "${CHAIN_STATE_DIR}" "${LIGHT_DIR}"

module purge >/dev/null 2>&1 || true
module load gcc/11.4.0 >/dev/null 2>&1 || true
module load intel/2024.2.0 >/dev/null 2>&1 || true
module load abaqus/2023 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true

echo "=== extract RF-U from existing ODB (abaqus python) ==="
abaqus python scripts/postprocessing/extract_rfu_from_odb.py \
  --odb "${ODB}" \
  --out "${OUT_DIR}/C2D_threads4_RF_U.csv" \
  > "${OUT_DIR}/extract_stdout.log" 2>&1
test -f "${OUT_DIR}/C2D_threads4_RF_U.csv"
wc -l "${OUT_DIR}/C2D_threads4_RF_U.csv"

echo "=== compare with system Python 3.11 ==="
python3 scripts/postprocessing/compare_threads_qualification.py \
  --cand-csv "${OUT_DIR}/C2D_threads4_RF_U.csv" \
  --ref-csv "${REF_CSV}" \
  --out-json "${OUT_DIR}/C2D_REQUALIFICATION_STATUS.json" \
  --out-csv "${OUT_DIR}/C2D_RF_U_COMPARISON.csv" \
  --out-report-md "${OUT_DIR}/C2D_REQUALIFICATION_REPORT.md" \
  --write-ok-marker "${CHAIN_STATE_DIR}/C2D.ok" \
  | tee "${OUT_DIR}/compare_stdout.log"

# Publish status into chain_state and light evidence
cp -f "${OUT_DIR}/C2D_REQUALIFICATION_STATUS.json" "${CHAIN_STATE_DIR}/C2D_STATUS.json"
cp -f "${OUT_DIR}/C2D_REQUALIFICATION_STATUS.json" \
      "${OUT_DIR}/C2D_REQUALIFICATION_REPORT.md" \
      "${OUT_DIR}/C2D_RF_U_COMPARISON.csv" \
      "${LIGHT_DIR}/" 2>/dev/null || true

python3 - <<PY
import json
from pathlib import Path
s = json.loads(Path("${OUT_DIR}/C2D_REQUALIFICATION_STATUS.json").read_text())
print("qualification_pass=", s.get("qualification_pass"))
print("rel_peak_force=", s.get("rel_peak_force"))
print("prepeak_nrmse=", s.get("prepeak_nrmse"))
if not s.get("qualification_pass"):
    raise SystemExit("C2D_REQUALIFICATION_FAILED")
assert Path("${CHAIN_STATE_DIR}/C2D.ok").is_file()
print("C2D.ok written")
PY

echo "C2D_REQUALIFICATION_DONE"
