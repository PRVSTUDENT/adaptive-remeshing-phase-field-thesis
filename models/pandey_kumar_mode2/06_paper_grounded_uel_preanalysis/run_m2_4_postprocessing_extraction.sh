#!/bin/bash
set -euo pipefail

WORKDIR="/scratch9/pr21vyci/runs/mode2_j2_adapted_fracture"
cd "$WORKDIR" || exit 1

PACKAGE_DIR="/home/pr21vyci/projects/mode2_reproduction_worktree/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis"
cp -u "$PACKAGE_DIR"/extract_mode2_adapted_fracture_terminal_evidence.py .

module purge
module load abaqus/2023

echo "=== EXECUTING GATE M2-4 TERMINAL POSTPROCESSING EXTRACTION ==="
abaqus python extract_mode2_adapted_fracture_terminal_evidence.py Job-2_UEL.odb .

echo "=== POSTPROCESSING EXTRACTION COMPLETE ==="
ls -lh mode2_j2_rf_history.csv mode2_j2_dmax_history.csv mode2_j2_crack_trajectory.csv MODE2_M2_4_TERMINAL_EXTRACTION_SUMMARY.json
