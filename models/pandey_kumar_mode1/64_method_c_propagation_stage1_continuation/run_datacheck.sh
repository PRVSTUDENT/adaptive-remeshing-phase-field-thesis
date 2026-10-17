#!/bin/bash
set -e
source /etc/profile.d/lmod.sh 2>/dev/null || true
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

export I_MPI_HYDRA_BOOTSTRAP=fork
export I_MPI_HYDRA_PMI=none
export I_MPI_HYDRA_BRANCH_COUNT=1
export OMPI_MCA_plm=isolated
export OMPI_MCA_ras=none

abaqus job=M1_MC_PROP_STAGE1_CONT_DC user=f42_mixed_uel.for input=M1_MC_PROP_STAGE1_CONT.inp datacheck cpus=1 scratch=. interactive
echo "DATACHECK_EXIT_CODE=$?"
