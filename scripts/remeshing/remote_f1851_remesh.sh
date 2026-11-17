#!/bin/bash
set -euo pipefail
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/f1838_case2_native_pilot
export F1851_HOME=$PWD
abaqus cae noGUI=remesh_f1851_existing.py -- f1851_case2_config.json PK_HOLE_COARSE_F1838_PILOT.odb f1851_original337_remesh Step-2
