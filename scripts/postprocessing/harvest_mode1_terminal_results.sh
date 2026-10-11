#!/bin/bash
# ==============================================================================
# harvest_mode1_terminal_results.sh
# ==============================================================================
# Authoritative Terminal Results Harvesting & Tri-Model Post-Processing Script
#
# Processes:
#   Job 1: 1411895.mmaster02 (Historical Stage 14 ET2 adapted mesh, 6,112 FE)
#   Job 2: 1411934.mmaster02 (Genuine Method B native adapted mesh, 14,677 FE)
#
# Can be run:
#   1. Standalone interactively from login node once jobs conclude.
#   2. Via PBS batch job chained with -W depend=afterany:1411895:1411934.
# ==============================================================================

set -euo pipefail

HARVEST_DIR="/scratch9/pr21vyci/runs/mode1_harvest"
RUN1_DIR="/scratch9/pr21vyci/runs/mode1_method_b_f1408/final_fracture"
RUN2_DIR="/scratch9/pr21vyci/runs/mode1_method_b_native_final"
OUT_DIR="${HARVEST_DIR}/results"

mkdir -p "${HARVEST_DIR}" "${OUT_DIR}"
cd "${HARVEST_DIR}"

echo "=========================================================="
echo "Starting Mode-I Fracture Harvesting Workflow"
echo "Timestamp: $(date -Iseconds)"
echo "Host:      $(hostname)"
echo "=========================================================="

# Load Abaqus environment
source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || true

# Copy latest extraction script
EXTRACTOR="${HARVEST_DIR}/extract_mode1_fracture_odb.py"
if [ -f "${RUN2_DIR}/extract_mode1_fracture_odb.py" ]; then
    cp -f "${RUN2_DIR}/extract_mode1_fracture_odb.py" "${EXTRACTOR}"
fi

echo "--- 1. Processing Historical Stage 14 ET2 (Job 1411895) ---"
if [ -f "${RUN1_DIR}/M1_MB_FINAL_1S.odb" ] && command -v abaqus >/dev/null 2>&1; then
    echo "Running Abaqus Python ODB extraction for Job 1411895..."
    abaqus python "${EXTRACTOR}" \
        --odb "${RUN1_DIR}/M1_MB_FINAL_1S.odb" \
        --dat "${RUN1_DIR}/M1_MB_FINAL_1S.dat" \
        --csv "${RUN1_DIR}/uel_energy_balance.csv" \
        --job-id "1411895.mmaster02" \
        --model-name "M1_MB_ET2_6K" \
        --out-dir "${OUT_DIR}" || true
else
    echo "Running Python3 DAT+CSV extraction for Job 1411895..."
    python3 "${EXTRACTOR}" \
        --dat "${RUN1_DIR}/M1_MB_FINAL_1S.dat" \
        --csv "${RUN1_DIR}/uel_energy_balance.csv" \
        --job-id "1411895.mmaster02" \
        --model-name "M1_MB_ET2_6K" \
        --out-dir "${OUT_DIR}" || true
fi

echo "--- 2. Processing Genuine Method B Native (Job 1411934) ---"
if [ -f "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.odb" ] && command -v abaqus >/dev/null 2>&1; then
    echo "Running Abaqus Python ODB extraction for Job 1411934..."
    abaqus python "${EXTRACTOR}" \
        --odb "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.odb" \
        --dat "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.dat" \
        --csv "${RUN2_DIR}/uel_energy_balance.csv" \
        --job-id "1411934.mmaster02" \
        --model-name "M1_MB_NATIVE_14K" \
        --out-dir "${OUT_DIR}" || true
else
    echo "Running Python3 DAT+CSV extraction for Job 1411934..."
    python3 "${EXTRACTOR}" \
        --dat "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.dat" \
        --csv "${RUN2_DIR}/uel_energy_balance.csv" \
        --job-id "1411934.mmaster02" \
        --model-name "M1_MB_NATIVE_14K" \
        --out-dir "${OUT_DIR}" || true
fi

echo "--- 3. Results Archive Listing ---"
ls -lh "${OUT_DIR}"

echo "=========================================================="
echo "Harvesting Complete: $(date -Iseconds)"
echo "=========================================================="
