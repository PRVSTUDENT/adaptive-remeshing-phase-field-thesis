#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/28_stage14_convergence_control_candidate
source /etc/profile.d/modules.sh 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || true

echo "=== RUNNING DATACHECK PK_M1_14K_CONV_CTRL_DATACHECK ==="
rm -f PK_M1_14K_CONV_CTRL_DATACHECK.lck PK_M1_14K_CONV_CTRL_DATACHECK.023
/cluster/application/abaqus/2023/Commands/abaqus datacheck job=PK_M1_14K_CONV_CTRL_DATACHECK input=PK_M1_14K_CONV_CTRL_DATACHECK.inp user=f42_mixed_uel.for memory="16gb" double=both interactive
EXIT_CODE=$?
echo "=== DATACHECK FINISHED WITH EXIT CODE: ${EXIT_CODE} ==="
exit "${EXIT_CODE}"
