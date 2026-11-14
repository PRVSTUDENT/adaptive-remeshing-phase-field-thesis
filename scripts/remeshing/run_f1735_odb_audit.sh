#!/bin/bash
set -euo pipefail
DIR="/scratch9/pr21vyci/runs/f1735_case2_adapted_fracture"
cd "$DIR"
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
echo "Running extract_f1735_case2_odb_sdv.py..."
abaqus python "$DIR/extract_f1735_case2_odb_sdv.py" "$DIR/PK_F1735_CASE_2_FRAC.odb" "$DIR/f1735_case2_final_frame_sdv.csv" "$DIR/f1735_case2_odb_summary.json"
echo "Extraction completed successfully."
