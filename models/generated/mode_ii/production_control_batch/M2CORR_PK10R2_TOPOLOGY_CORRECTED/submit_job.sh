#!/bin/bash
#PBS -N M2PK10R2_CORR
#PBS -q entry_imfdfkmq
#PBS -l nodes=1:ppn=1
#PBS -l mem=16gb
#PBS -l walltime=24:00:00
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
#PBS -m abe
#PBS -o M2PK10R2_CORR.out
#PBS -e M2PK10R2_CORR.err

set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

cd "$PBS_O_WORKDIR" || exit 1

# Fail-closed notification source and config load
if [ ! -f "./job_notifications.sh" ]; then
  echo "[LAUNCHER ERROR] job_notifications.sh missing" >&2
  exit 10
fi

# shellcheck disable=SC1091
source ./job_notifications.sh

notification_load_config || {
  echo "[LAUNCHER ERROR] notification_load_config failed" >&2
  exit 11
}

# Install terminal traps (COMPLETED / FAILED / TERMINATED)
notification_install_terminal_trap

# Send START notification
notify_start

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING M2CORR_PK10R2_TOPOLOGY_CORRECTED ==="
abaqus job=M2CORR_PK10R2_TOPOLOGY_CORRECTED user=f42_mixed_uel.for input=M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp double=both interactive
ABAQUS_EXIT=$?
echo "=== FINISHED M2CORR_PK10R2_TOPOLOGY_CORRECTED (EXIT: $ABAQUS_EXIT) ==="

exit "$ABAQUS_EXIT"
