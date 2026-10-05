#!/bin/bash
#PBS -N entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -e
cd "$PBS_O_WORKDIR"

# Source dual-channel notifications
NOTIFICATION_SCRIPT="$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
if [ -f "$NOTIFICATION_SCRIPT" ]; then
    source "$NOTIFICATION_SCRIPT"
    notification_install_terminal_trap
    notify_start "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"
fi

export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH
source /etc/profile.d/lmod.sh 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Starting Abaqus Same-Mesh Restart Validation Job M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION..."
/cluster/application/abaqus/2023/Commands/abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION user=f43_mixed_uel_restart_capable.for input=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp double=both interactive
echo "Abaqus job completed successfully."
