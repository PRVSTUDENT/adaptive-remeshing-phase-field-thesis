#!/bin/bash
# Notification-only helper: no scheduler commands.
set -euo pipefail
[[ $# == 3 && "$1" =~ ^/scratch9/pr21vyci/runs/mode1_[a-z0-9_/]+$ && "$1" != *..* ]] || exit 64
[[ "$2" =~ ^[0-9]+\.mmaster02$ && "$3" =~ ^M1_[A-Z0-9_]+$ ]] || exit 64
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "$1/job_notifications.sh"
notification_load_config
notify_submitted "$2" "$3" entry_imfdfkmq
