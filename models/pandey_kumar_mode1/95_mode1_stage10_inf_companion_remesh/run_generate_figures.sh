#!/bin/bash
set -e
module load python/gcc/11.4.0/3.11.7
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/95_mode1_stage10_inf_companion_remesh
mkdir -p ../../../results/figures/mode1_gate6b
python3 generate_stage10_figures.py STAGE10_INF_COMPANION_REMESH_SUMMARY.json stage10_adapted_elements.csv ../../../results/figures/mode1_gate6b
echo "Figures generated successfully!"
