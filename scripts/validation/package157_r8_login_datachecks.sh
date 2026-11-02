#!/bin/bash
set -euo pipefail
RUN_DIR=/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r8
if ! type module >/dev/null 2>&1; then
 source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
python3 "${RUN_DIR}/runtime/scripts/state_transfer/driver_package157_r8.py" --package "${RUN_DIR}" --output "${RUN_DIR}/unused_startup" --extractor "${RUN_DIR}/runtime/scripts/validation/extract_package148_iteration.py" --startup-only > "${RUN_DIR}/login_startup.json"
bash "${RUN_DIR}/run_datacheck.sh" "${RUN_DIR}"
