#!/bin/bash
set -euo pipefail

# ==============================================================================
# Gate-6B Post-S1 Batch Release Execution Script
# Phase: MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE
# Execution Mode: 1-CPU Serial for all 6 candidates
# ==============================================================================

BASE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1"

echo "================================================================================"
echo "DISPATCHING GATE-6B POST-S1 BATCH SUBMISSIONS (6 CANDIDATES)"
echo "Timestamp: $(date -Iseconds)"
echo "================================================================================"

# 1. S2 (32k mesh, h=0.0020 mm)
echo -n "Submitting S2 (PK_M1_S2_ENERGY)... "
cd "${BASE_DIR}/12_fixed_convergence_h0020"
JOB_S2=$(qsub submit_solver.pbs)
echo "SUBMITTED: ${JOB_S2}"

# 2. S3 (42k mesh, h=0.0015 mm)
echo -n "Submitting S3 (PK_M1_S3_ENERGY)... "
cd "${BASE_DIR}/13_fixed_convergence_h0015"
JOB_S3=$(qsub submit_solver.pbs)
echo "SUBMITTED: ${JOB_S3}"

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
echo "BATCH SUBMISSION SUMMARY:"
echo "  S2: ${JOB_S2}"
echo "  S3: ${JOB_S3}"
echo "  T1: ${JOB_T1}"
echo "  T3: ${JOB_T3}"
echo "  L2: ${JOB_L2}"
echo "  L3: ${JOB_L3}"
echo "================================================================================"
