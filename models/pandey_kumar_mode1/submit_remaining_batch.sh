#!/bin/bash
set -euo pipefail

BASE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1"

echo "================================================================================"
echo "DISPATCHING REMAINING GATE-6B BATCH SUBMISSIONS (T1, T3, L2, L3)"
echo "Timestamp: $(date -Iseconds)"
echo "================================================================================"

# 3. T1 (Temporal coarse, dt=1.0e-3)
echo -n "Submitting T1 (PK_MODE1_T1_COARSE_ENERGY)... "
cd "${BASE_DIR}/17_temporal_convergence_t1_coarse"
JOB_T1=$(qsub submit_solver.pbs)
echo "SUBMITTED: ${JOB_T1}"

# 4. T3 (Temporal fine, dt=2.5e-4)
echo -n "Submitting T3 (PK_MODE1_T3_FINE_ENERGY)... "
cd "${BASE_DIR}/19_temporal_convergence_t3_fine"
JOB_T3=$(qsub submit_solver.pbs)
echo "SUBMITTED: ${JOB_T3}"

# 5. L2 (Length scale intermediate, l0=0.01125 mm)
echo -n "Submitting L2 (PK_M1_L2_L01125_ENERGY)... "
cd "${BASE_DIR}/21_length_scale_l2_intermediate"
JOB_L2=$(qsub submit_solver.pbs)
echo "SUBMITTED: ${JOB_L2}"

# 6. L3 (Length scale coarse, l0=0.01500 mm)
echo -n "Submitting L3 (PK_M1_L3_L01500_ENERGY)... "
cd "${BASE_DIR}/22_length_scale_l3_coarse"
JOB_L3=$(qsub submit_solver.pbs)
echo "SUBMITTED: ${JOB_L3}"

echo "================================================================================"
echo "REMAINING BATCH SUBMISSION COMPLETE"
echo "================================================================================"
