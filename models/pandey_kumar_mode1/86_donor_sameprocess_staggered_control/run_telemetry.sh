#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_package86_donor_sameprocess_staggered
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load abaqus/2023
abaqus python extract_pkg86_sameprocess_telemetry.py M1_DONOR_SAMEPROCESS_STAGGERED.odb uel_energy_balance.csv pkg86_telemetry_summary.json
