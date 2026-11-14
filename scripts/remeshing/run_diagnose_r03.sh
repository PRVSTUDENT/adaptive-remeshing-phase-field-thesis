#!/bin/bash
set -euo pipefail
source /etc/profile.d/lmod.sh
module purge || true
module load gcc/11.4.0 || true
module load intel/2024.2.0 || true
module load abaqus/2023 || module load abaqus || true
cd /scratch9/pr21vyci/runs/f1735_case2_adapted_fracture
abaqus python diagnose_f1753_r03_damage_violation.py PK_F1735_CASE_2_FRAC.odb f1753_r03_damage_violation_diagnostic.json
