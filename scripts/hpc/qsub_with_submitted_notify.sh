#!/bin/bash
# Run qsub and immediately send the login-side Telegram SUBMITTED event.
#
# Usage:
#   scripts/hpc/qsub_with_submitted_notify.sh \
#     --job-name t5_h0_smoke \
#     --message "Queue: entry_imfdfkmq; CPUs: 4; memory: 16 GB; walltime: 01:00:00" \
#     -- -q entry_imfdfkmq -M user@example.edu -m abe script.pbs
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
JOB_NAME=""
MESSAGE=""

usage() {
  sed -n '2,11p' "$0" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --job-name)
      JOB_NAME="${2:-}"
      shift 2
      ;;
    --message)
      MESSAGE="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "unknown argument before --: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "${JOB_NAME}" ] || [ -z "${MESSAGE}" ] || [ "$#" -eq 0 ]; then
  echo "missing --job-name, --message, or qsub arguments after --" >&2
  usage
  exit 2
fi

cd "${PROJECT_HOME}"

JOB_ID="$(qsub "$@")"
printf '%s\n' "${JOB_ID}"

python3 scripts/hpc/telegram_notify.py \
  --event SUBMITTED \
  --job-id "${JOB_ID}" \
  --job-name "${JOB_NAME}" \
  --message "${MESSAGE}" \
  >&2 \
  || true
