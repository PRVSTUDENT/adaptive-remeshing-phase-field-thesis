#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_candidate_c2_peak_preserved_reequilibration"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running test_stab_c2 execution..."
rm -f test_stab_c2.lck test_stab_c2.log test_stab_c2.dat test_stab_c2.msg test_stab_c2.sta test_stab_c2.prt test_stab_c2.odb
abaqus job=test_stab_c2 input=test_stab_c2.inp user=f42_mixed_uel.for cpus=1 interactive
EXIT_CODE=$?
echo "test_stab_c2 finished with Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
