#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_pk_f1714_five_hole

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Starting Abaqus 2023 1-Element Compiled Amor UEL Test ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

# Clean output artifacts, preserving .inp
rm -f PK_F1714_1ELEM_AMOR_TEST.log PK_F1714_1ELEM_AMOR_TEST.dat PK_F1714_1ELEM_AMOR_TEST.msg PK_F1714_1ELEM_AMOR_TEST.odb PK_F1714_1ELEM_AMOR_TEST.sta PK_F1714_1ELEM_AMOR_TEST.prt PK_F1714_1ELEM_AMOR_TEST.com PK_F1714_1ELEM_AMOR_TEST.sim PK_F1714_1ELEM_AMOR_TEST.stt PK_F1714_1ELEM_AMOR_TEST.mdl

set +e
abaqus job=PK_F1714_1ELEM_AMOR_TEST input=PK_F1714_1ELEM_AMOR_TEST.inp user=f42_amor_split_uel.for interactive
EXIT_CODE=$?
set -e

echo "=== 1-Element Solve Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
