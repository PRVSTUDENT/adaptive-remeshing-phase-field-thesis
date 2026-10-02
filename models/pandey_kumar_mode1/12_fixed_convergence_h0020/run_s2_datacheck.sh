#!/bin/bash
set -eo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/12_fixed_convergence_h0020
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING DATACHECK S2 (32,130 elements) ==="
rm -f PK_M1_S2_DC.*
abaqus datacheck job=PK_M1_S2_DC user=f42_mixed_uel.for input=PK_MODE1_FIX_H0020_ENERGY.inp cpus=1 memory=16gb double=both interactive
RC=$?
echo "=== DATACHECK S2 FINISHED WITH EXIT CODE: $RC ==="
exit $RC
