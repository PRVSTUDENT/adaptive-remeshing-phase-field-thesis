#!/bin/bash
# Bounded login-node SUBMITTED delivery; never invokes the scheduler.
set -euo pipefail
[[ $# == 2 && "$1" =~ ^[0-9]+\.mmaster02$ ]] || exit 64
[[ "$2" == M1_MB_RST_PROD || "$2" == M1_MB_RST_DIAG ]] || exit 64
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source /scratch9/pr21vyci/runs/mode1_package48_restart_control/job_notifications.sh
notification_load_config
notify_submitted "$1" "$2" entry_imfdfkmq
