#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_candidate_c2_peak_preserved_reequilibration"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Loaded environment. ifort path: $(command -v ifort)"
echo "Running Abaqus 2023 Datacheck on M1_C2_PEAK_PRESERVED_REEQUIL.inp..."

rm -f M1_C2_PEAK_PRESERVED_REEQUIL_DC.lck M1_C2_PEAK_PRESERVED_REEQUIL_DC.log M1_C2_PEAK_PRESERVED_REEQUIL_DC.dat M1_C2_PEAK_PRESERVED_REEQUIL_DC.msg M1_C2_PEAK_PRESERVED_REEQUIL_DC.sta M1_C2_PEAK_PRESERVED_REEQUIL_DC.prt

abaqus job=M1_C2_PEAK_PRESERVED_REEQUIL_DC input=M1_C2_PEAK_PRESERVED_REEQUIL.inp user=f42_mixed_uel.for datacheck interactive
EXIT_CODE=$?

echo "Datacheck Finished with Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
