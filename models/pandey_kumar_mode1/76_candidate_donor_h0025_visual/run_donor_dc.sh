#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

rm -f M1_CANDIDATE_DONOR_H0025_VISUAL_DC.*

abaqus job=M1_CANDIDATE_DONOR_H0025_VISUAL_DC input=candidate_donor_h0025_visual.inp user=f42_mixed_uel.for datacheck interactive
EXIT_CODE=$?
echo "DATACHECK_EXIT_CODE: ${EXIT_CODE}"
tail -n 25 M1_CANDIDATE_DONOR_H0025_VISUAL_DC.dat
exit ${EXIT_CODE}
