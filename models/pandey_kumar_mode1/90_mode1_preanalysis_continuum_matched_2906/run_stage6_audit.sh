#!/bin/bash
set -euo pipefail

WORKDIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906"
cd "${WORKDIR}"

module purge || true
module load gcc/11.4.0 || true
module load abaqus/2023 || true

echo "Starting Stage 6 Output-Position and Stress-Recovery Audit..."
abaqus python stage6_output_recovery_audit.py

echo "Stage 6 Audit finished successfully."
