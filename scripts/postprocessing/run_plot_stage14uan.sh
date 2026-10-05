#!/bin/bash
source /etc/profile
module purge
module load gcc/11.4.0
module load python/gcc/11.4.0/3.11.7 || true

cd /home/pr21vyci/projects/adaptive-remeshing
python3 scripts/postprocessing/plot_stage14uan_determinism_and_temporal.py
