#!/bin/bash
set -euo pipefail
module purge || true
module load gcc/11.4.0 || true
module load abaqus/2023 || true
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906
abaqus python extract_package90_control_miseseri.py
