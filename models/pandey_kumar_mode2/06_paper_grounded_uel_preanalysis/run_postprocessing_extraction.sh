#!/bin/bash
# ==============================================================================
# run_postprocessing_extraction.sh
# Post-processing extraction runner for Job-1_UEL_paper_horizon (Gate M2-2)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SCRATCH_DIR="/scratch9/pr21vyci/runs/mode2_j1_miehe_horizon"
ODB_FILE="$SCRATCH_DIR/Job-1_UEL_paper_horizon.odb"

if [ ! -f "$ODB_FILE" ]; then
    echo "[ERROR] ODB not found in scratch: $ODB_FILE" >&2
    exit 1
fi

echo "=== STARTING MODE-II GATE M2-2 TERMINAL EXTRACTION ==="
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

# Run Abaqus Python ODB extractor
abaqus python extract_mode2_paper_horizon_terminal_evidence.py "$ODB_FILE" "$SCRIPT_DIR"

# Run Python 3 figure generator
if command -v python3 >/dev/null 2>&1; then
    python3 ../../../scripts/postprocessing/plot_mode2_paper_horizon_evolution.py "$SCRIPT_DIR" "$SCRIPT_DIR/../../../results/figures/mode2/mode2_paper_horizon_miseseri_damage_evolution.png" || true
fi

echo "=== FINISHED MODE-II GATE M2-2 TERMINAL EXTRACTION ==="
