#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot
echo "=== Starting Abaqus Datacheck for Task F1722 Causal Pilot ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
command -v ifort
command -v abaqus
set +e
abaqus job=M1_PK_F1722_DATACHECK input=PK_F1721_CAUSAL_PILOT.inp user=f1721_proposed_staggered_coupling_uel.for datacheck interactive
RC=$?
set -e
echo "=== Abaqus Datacheck Finished with Exit Code: ${RC} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${RC}
