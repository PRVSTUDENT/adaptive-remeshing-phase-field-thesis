#!/bin/bash
set -euo pipefail
RUN=/scratch9/pr21vyci/runs/mode1_c4_exact_load_reference
OUT="$RUN/package160_recovery_endpoint.json"
test -f "$RUN/M1_C4_EXACT_REF.odb"
test ! -e "$OUT"
if ! type module >/dev/null 2>&1; then
 source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python "$RUN/extract_recovery_endpoint.py" "$RUN"
