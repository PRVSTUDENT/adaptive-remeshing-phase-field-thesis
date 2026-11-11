#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_pk_f1716_five_hole_pilot

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running Controlled Physical Pilot Simulation ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

# Clean any previous artifacts
rm -f PK_F1716_PILOT.lck PK_F1716_PILOT.odb PK_F1716_PILOT.dat PK_F1716_PILOT.msg PK_F1716_PILOT.sta PK_F1716_PILOT.com PK_F1716_PILOT.log uel_energy_balance.csv

# Run interactive Abaqus job
set +e
abaqus job=PK_F1716_PILOT input=PK_F1716_PILOT_PHYSICAL.inp user=f42_amor_split_uel_v2.for interactive
EXIT_CODE=$?
set -e

echo "=== Pilot Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
