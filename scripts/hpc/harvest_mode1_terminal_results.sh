#!/bin/bash
# ==============================================================================
# harvest_mode1_terminal_results.sh
# ==============================================================================
# Authoritative Terminal Results Harvesting & Tri-Model Post-Processing Script
#
# Processes:
#   Job 1: 1411895.mmaster02 (Historical Stage 14 ET2 adapted mesh, 6,112 FE, 1-CPU Serial)
#   Job 2: 1411934.mmaster02 (Genuine Method B native adapted mesh, 14,677 FE, 1-CPU Serial)
#   Job 3: 1411949.mmaster02 (Genuine Method B native adapted mesh, 14,677 FE, 8-Thread SMP)
#   Job 4: 1411950.mmaster02 (Historical Stage 14 ET2 adapted mesh, 6,112 FE, 8-Thread SMP)
#
# Usage:
#   ./harvest_mode1_terminal_results.sh [all|1|2|3|4]
# ==============================================================================

set -euo pipefail

TARGET_JOB="${1:-all}"

HARVEST_DIR="/scratch9/pr21vyci/runs/mode1_harvest"
RUN1_DIR="/scratch9/pr21vyci/runs/mode1_method_b_f1408/final_fracture"
RUN2_DIR="/scratch9/pr21vyci/runs/mode1_method_b_native_final"
RUN3_DIR="/scratch9/pr21vyci/runs/mode1_method_b_native_8t_a"
RUN4_DIR="/scratch9/pr21vyci/runs/mode1_et2_8t_a"
OUT_DIR="${HARVEST_DIR}/results"

mkdir -p "${HARVEST_DIR}" "${OUT_DIR}"
cd "${HARVEST_DIR}"

echo "=========================================================="
echo "Starting Mode-I Fracture Harvesting Workflow (Target: ${TARGET_JOB})"
echo "Timestamp: $(date -Iseconds)"
echo "Host:      $(hostname)"
echo "=========================================================="

# Load Abaqus environment
source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || true

EXTRACTOR="${HARVEST_DIR}/extract_mode1_fracture_odb.py"

# --- 1. Processing Historical Stage 14 ET2 Serial (Job 1411895) ---
if [ "${TARGET_JOB}" = "all" ] || [ "${TARGET_JOB}" = "1" ]; then
    echo "--- 1. Processing Historical Stage 14 ET2 Serial (Job 1411895) ---"
    if [ -f "${RUN1_DIR}/M1_MB_FINAL_1S.odb" ] && command -v abaqus >/dev/null 2>&1; then
        echo "Running Abaqus Python ODB extraction for Job 1411895..."
        abaqus python "${EXTRACTOR}" \
            --odb "${RUN1_DIR}/M1_MB_FINAL_1S.odb" \
            --dat "${RUN1_DIR}/M1_MB_FINAL_1S.dat" \
            --csv "${RUN1_DIR}/uel_energy_balance.csv" \
            --job-id "1411895.mmaster02" \
            --model-name "M1_MB_ET2_6K_1S" \
            --out-dir "${OUT_DIR}" || true
    elif [ -f "${RUN1_DIR}/M1_MB_FINAL_1S.dat" ]; then
        echo "Running Python3 DAT+CSV extraction for Job 1411895..."
        python3 "${EXTRACTOR}" \
            --dat "${RUN1_DIR}/M1_MB_FINAL_1S.dat" \
            --csv "${RUN1_DIR}/uel_energy_balance.csv" \
            --job-id "1411895.mmaster02" \
            --model-name "M1_MB_ET2_6K_1S" \
            --out-dir "${OUT_DIR}" || true
    fi
fi

# --- 2. Processing Genuine Method B Native Serial (Job 1411934) ---
if [ "${TARGET_JOB}" = "all" ] || [ "${TARGET_JOB}" = "2" ]; then
    echo "--- 2. Processing Genuine Method B Native Serial (Job 1411934) ---"
    if [ -f "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.odb" ] && command -v abaqus >/dev/null 2>&1; then
        echo "Running Abaqus Python ODB extraction for Job 1411934..."
        abaqus python "${EXTRACTOR}" \
            --odb "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.odb" \
            --dat "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.dat" \
            --csv "${RUN2_DIR}/uel_energy_balance.csv" \
            --job-id "1411934.mmaster02" \
            --model-name "M1_MB_NATIVE_14K_1S" \
            --out-dir "${OUT_DIR}" || true
    elif [ -f "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.dat" ]; then
        echo "Running Python3 DAT+CSV extraction for Job 1411934..."
        python3 "${EXTRACTOR}" \
            --dat "${RUN2_DIR}/M1_MB_NATIVE_FINAL_1S.dat" \
            --csv "${RUN2_DIR}/uel_energy_balance.csv" \
            --job-id "1411934.mmaster02" \
            --model-name "M1_MB_NATIVE_14K_1S" \
            --out-dir "${OUT_DIR}" || true
    fi
fi

# --- 3. Processing Genuine Method B Native 8-Thread SMP (Job 1411949) ---
if [ "${TARGET_JOB}" = "all" ] || [ "${TARGET_JOB}" = "3" ]; then
    echo "--- 3. Processing Genuine Method B Native 8-Thread SMP (Job 1411949) ---"
    if [ -f "${RUN3_DIR}/M1_MB_NATIVE_8T_A.odb" ] && command -v abaqus >/dev/null 2>&1; then
        echo "Running Abaqus Python ODB extraction for Job 1411949..."
        abaqus python "${EXTRACTOR}" \
            --odb "${RUN3_DIR}/M1_MB_NATIVE_8T_A.odb" \
            --dat "${RUN3_DIR}/M1_MB_NATIVE_8T_A.dat" \
            --csv "${RUN3_DIR}/uel_energy_balance.csv" \
            --job-id "1411949.mmaster02" \
            --model-name "M1_MB_NATIVE_14K_8T_A" \
            --out-dir "${OUT_DIR}" || true
    elif [ -f "${RUN3_DIR}/M1_MB_NATIVE_8T_A.dat" ]; then
        echo "Running Python3 DAT+CSV extraction for Job 1411949..."
        python3 "${EXTRACTOR}" \
            --dat "${RUN3_DIR}/M1_MB_NATIVE_8T_A.dat" \
            --csv "${RUN3_DIR}/uel_energy_balance.csv" \
            --job-id "1411949.mmaster02" \
            --model-name "M1_MB_NATIVE_14K_8T_A" \
            --out-dir "${OUT_DIR}" || true
    fi
fi

# --- 4. Processing Historical Stage 14 ET2 8-Thread SMP (Job 1411950) ---
if [ "${TARGET_JOB}" = "all" ] || [ "${TARGET_JOB}" = "4" ]; then
    echo "--- 4. Processing Historical Stage 14 ET2 8-Thread SMP (Job 1411950) ---"
    if [ -f "${RUN4_DIR}/M1_ET2_8T_A.odb" ] && command -v abaqus >/dev/null 2>&1; then
        echo "Running Abaqus Python ODB extraction for Job 1411950..."
        abaqus python "${EXTRACTOR}" \
            --odb "${RUN4_DIR}/M1_ET2_8T_A.odb" \
            --dat "${RUN4_DIR}/M1_ET2_8T_A.dat" \
            --csv "${RUN4_DIR}/uel_energy_balance.csv" \
            --job-id "1411950.mmaster02" \
            --model-name "M1_MB_ET2_6K_8T_A" \
            --out-dir "${OUT_DIR}" || true
    elif [ -f "${RUN4_DIR}/M1_ET2_8T_A.dat" ]; then
        echo "Running Python3 DAT+CSV extraction for Job 1411950..."
        python3 "${EXTRACTOR}" \
            --dat "${RUN4_DIR}/M1_ET2_8T_A.dat" \
            --csv "${RUN4_DIR}/uel_energy_balance.csv" \
            --job-id "1411950.mmaster02" \
            --model-name "M1_MB_ET2_6K_8T_A" \
            --out-dir "${OUT_DIR}" || true
    fi
fi

echo "--- 5. Results Archive Listing ---"
ls -lh "${OUT_DIR}"

echo "=========================================================="
echo "Harvesting Complete: $(date -Iseconds)"
echo "=========================================================="
