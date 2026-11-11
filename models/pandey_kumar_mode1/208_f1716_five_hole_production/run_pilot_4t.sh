#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_pk_f1716_five_hole_pilot

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running 4-Thread Controlled Physical Pilot Simulation ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

rm -f PK_F1716_PILOT_4T.lck PK_F1716_PILOT_4T.odb PK_F1716_PILOT_4T.dat PK_F1716_PILOT_4T.msg PK_F1716_PILOT_4T.sta PK_F1716_PILOT_4T.com PK_F1716_PILOT_4T.log uel_energy_balance_4t.csv

set +e
abaqus job=PK_F1716_PILOT_4T input=PK_F1716_PILOT_PHYSICAL.inp user=f42_amor_split_uel_v2.for cpus=4 mp_mode=threads interactive
EXIT_CODE=$?
set -e

echo "=== 4-Thread Pilot Finished with Exit Code: ${EXIT_CODE} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
exit ${EXIT_CODE}
