#!/bin/bash
source /etc/profile.d/lmod.sh 2>/dev/null || true
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

RUN_DIR="/scratch9/pr21vyci/runs/mode1_stage_c1_2_propagation_s2_recon_diag"
cd "${RUN_DIR}"

JOB="M1_MC_PROP_S2_RECON_DIAG_DC"
INP="M1_MC_PROP_S2_RECON_DIAG.inp"
USER="f42_mixed_uel.for"

abaqus job="${JOB}" input="${INP}" user="${USER}" datacheck cpus=1 interactive
EXIT_CODE=$?
echo "DATACHECK_EXIT=${EXIT_CODE}"
exit ${EXIT_CODE}
