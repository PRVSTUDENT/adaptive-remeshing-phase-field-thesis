#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/f1730_case2_recovery_solve
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_case2_recovery_miseseri.py --odb PK_HOLE_COMPANION_RECOVERY.odb --output f1730_case2_recovery_telemetry.json
