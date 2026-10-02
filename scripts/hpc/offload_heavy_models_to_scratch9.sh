#!/usr/bin/env bash
# ==============================================================================
# Script: offload_heavy_models_to_scratch9.sh
# Purpose: Safe targeted offload of heavy completed Abaqus ODB files (>10 GB)
#          from /home/pr21vyci/projects/adaptive-remeshing to
#          /scratch9/pr21vyci/home_offload/ with symbolic links.
#
# GOVERNANCE RULES:
#   1. NEVER touch or move Job 1399632 (canonical nominal-1% twin for Gate 6).
#   2. NEVER touch or move active Gate-6 running directory (22_gate6_adaptive_cpe4_5pct).
#   3. NEVER touch .inp, .for, .py, .json, .csv files.
#   4. Use DRY_RUN=1 by default for verification. Set DRY_RUN=0 for real execution.
# ==============================================================================

set -Eeuo pipefail

DRY_RUN="${DRY_RUN:-1}"
USER_NAME="${USER:-pr21vyci}"
SCRATCH_BASE="/scratch9/${USER_NAME}/home_offload"
RUN_TAG="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${HOME}/hpc_storage_cleanup_logs"
MANIFEST="${LOG_DIR}/offload_scratch9_manifest_${RUN_TAG}.tsv"

mkdir -p "${SCRATCH_BASE}" "${LOG_DIR}"

echo "=============================================================================="
echo "SAFE OFFLOAD TO SCRATCH9"
echo "Timestamp: $(date -Iseconds)"
echo "Mode: DRY_RUN=${DRY_RUN}"
echo "Destination: ${SCRATCH_BASE}"
echo "Manifest: ${MANIFEST}"
echo "=============================================================================="

# Explicit list of approved offload candidates (>10 GB completed ODBs)
CANDIDATES=(
    "models/pandey_kumar_mode1/20_fixed_convergence_h00100_th4/PK_M1_FIX_H00100_TH4.odb"
    "models/pandey_kumar_mode1/18_fixed_convergence_h00100_serial/PK_M1_FIX_H00100.odb"
    "models/pandey_kumar_mode1/19_fixed_convergence_h00125_th4/PK_M1_FIX_H00125_TH4.odb"
    "models/pandey_kumar_mode1/17_fixed_convergence_h00125_serial/PK_M1_FIX_H00125.odb"
    "models/pandey_kumar_mode1/02_proposed_adaptive_refined/predecessor_1398865/PK_MODE1_PROPOSED_PFM.odb"
    "models/pandey_kumar_mode1/13_fixed_convergence_h0015/PK_M1_FIX_H0015_VIS.odb"
    "models/pandey_kumar_mode1/12_fixed_convergence_h0020/PK_M1_FIX_H0020_VIS.odb"
    "models/pandey_kumar_mode1/16_thread_determinism_h0030_r2/PK_M1_FIX_H0030_TH4_R2.odb"
    "models/pandey_kumar_mode1/15_thread_qualification_h0030/PK_M1_FIX_H0030_TH4.odb"
    "models/pandey_kumar_mode1/11_fixed_convergence_h0030/PK_M1_FIX_H0030_VIS.odb"
    "models/abaquser_visualization/task6_production_2pct_vis/PK_MODE1_PROPOSED_PFM_VIS.odb"
    "models/pandey_kumar_mode1/06_production_adaptive_2pct/PK_MODE1_PROPOSED_PFM.odb"
    "models/pandey_kumar_mode1/08_task7_inc_sens_2x/PK_M1_2P_INC2X.odb"
    "models/pandey_kumar_mode1/09_task7_mesh_sens_3pct/PK_M1_3P_PFM.odb"
    "models/pandey_kumar_mode1/07_production_adaptive_5pct/PK_MODE1_5PCT_PFM.odb"
    "models/pandey_kumar_mode1/10_fixed_mesh_refinement_h0015/PK_MODE1_STANDARD_PFM.odb"
)

# Strict protection guard
is_protected() {
    local target="$1"
    if [[ "$target" == *"predecessor_1399632"* ]]; then
        return 0
    fi
    if [[ "$target" == *"22_gate6_adaptive_cpe4_5pct"* ]]; then
        return 0
    fi
    return 1
}

PROJECT_ROOT="/home/${USER_NAME}/projects/adaptive-remeshing"
cd "${PROJECT_ROOT}"

echo -e "status\tbytes\tsource_path\tdestination_path" > "${MANIFEST}"

total_bytes=0
count=0

for rel_path in "${CANDIDATES[@]}"; do
    src="${PROJECT_ROOT}/${rel_path}"

    if is_protected "${rel_path}"; then
        echo "PROTECTED (Skipping): ${rel_path}"
        echo -e "PROTECTED_SKIPPED\t0\t${src}\tNONE" >> "${MANIFEST}"
        continue
    fi

    if [ ! -f "${src}" ]; then
        echo "NOT_FOUND (Skipping): ${rel_path}"
        continue
    fi

    if [ -L "${src}" ]; then
        echo "ALREADY_SYMLINK (Skipping): ${rel_path}"
        echo -e "ALREADY_SYMLINK\t0\t${src}\t$(readlink "${src}")" >> "${MANIFEST}"
        continue
    fi

    dst="${SCRATCH_BASE}/${rel_path}"
    dst_dir="$(dirname "${dst}")"
    mkdir -p "${dst_dir}"

    bytes="$(stat -c '%s' "${src}" 2>/dev/null || echo 0)"
    total_bytes=$((total_bytes + bytes))
    count=$((count + 1))
    size_gb="$(awk "BEGIN {printf \"%.2f\", ${bytes}/1073741824}")"

    if [ "${DRY_RUN}" = "1" ]; then
        echo "[DRY-RUN] Would move: ${rel_path} (${size_gb} GB)"
        echo "          -> ${dst}"
        echo "          and link: ${src} -> ${dst}"
        echo -e "DRY_RUN_PLANNED\t${bytes}\t${src}\t${dst}" >> "${MANIFEST}"
    else
        echo "[OFFLOAD] Moving: ${rel_path} (${size_gb} GB) -> ${dst}"
        mv "${src}" "${dst}"
        ln -s "${dst}" "${src}"
        echo "          Symlink created: ${src} -> ${dst}"
        echo -e "OFFLOADED_AND_LINKED\t${bytes}\t${src}\t${dst}" >> "${MANIFEST}"
    fi
done

total_gb="$(awk "BEGIN {printf \"%.2f\", ${total_bytes}/1073741824}")"
echo "=============================================================================="
echo "Scan Summary:"
echo "Files Processed: ${count}"
echo "Total Volume: ${total_gb} GB"
echo "Manifest written to: ${MANIFEST}"
echo "=============================================================================="
