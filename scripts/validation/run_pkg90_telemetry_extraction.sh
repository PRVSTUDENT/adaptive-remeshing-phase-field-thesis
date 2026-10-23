#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package90_c3_transfer"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Extracting Package 90 ODB telemetry..."
abaqus python extract_pkg90_results.py
echo "Extraction completed with exit code: $?"
