#!/bin/bash
set -euo pipefail
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/f1838_case2_native_pilot
abaqus python export_f1851_fields.py PK_HOLE_COARSE_F1838_PILOT.odb Step-2 300 f1851_original300.json
abaqus python export_f1851_fields.py PK_HOLE_COARSE_F1838_PILOT.odb Step-2 337 f1851_original337.json
