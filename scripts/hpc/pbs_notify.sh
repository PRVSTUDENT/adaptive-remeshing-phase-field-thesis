# Shared PBS begin/end notifications: Telegram primary, email secondary.
# Source from PBS scripts after PROJECT_HOME is set.
#
#   source "${PROJECT_HOME}/scripts/hpc/pbs_notify.sh"
#   pbs_notify_install_traps
#   pbs_notify_begin
#
# Optional: set PBS_NOTIFY_SKIP_EMAIL=1 once Telegram is verified.

_PBS_NOTIFY_START_EPOCH="$(date +%s 2>/dev/null || echo 0)"
_PBS_NOTIFIER="${PROJECT_HOME:-$HOME/projects/adaptive-remeshing}/scripts/hpc/telegram_notify.py"
_PBS_MAIL_HELPER="${PROJECT_HOME:-$HOME/projects/adaptive-remeshing}/scripts/hpc/pbs_job_mail_notify.sh"

# shellcheck disable=SC1090
[ -f "${_PBS_MAIL_HELPER}" ] && . "${_PBS_MAIL_HELPER}" 2>/dev/null || true

pbs_notify_telegram() {
  local event="$1"
  local message="${2:-}"
  if [ -x "$(command -v python3 2>/dev/null)" ] && [ -f "${_PBS_NOTIFIER}" ]; then
    python3 "${_PBS_NOTIFIER}" \
      --event "${event}" \
      --job-id "${PBS_JOBID:-unknown}" \
      --job-name "${PBS_JOBNAME:-unknown}" \
      --message "${message}" \
      >/dev/null 2>&1 || true
  fi
}

pbs_notify_begin() {
  local host
  host="$(hostname 2>/dev/null || echo unknown)"
  pbs_notify_telegram "BEGIN" \
    "Host: ${host}; queue: ${PBS_QUEUE:-unknown}; workdir: ${PBS_O_WORKDIR:-unknown}; time: $(date -Is 2>/dev/null || date)"
  if [ "${PBS_NOTIFY_SKIP_EMAIL:-0}" != "1" ] && type pbs_mail_begin >/dev/null 2>&1; then
    pbs_mail_begin || true
  fi
}

pbs_notify_skipped() {
  local reason="${1:-missing upstream marker}"
  pbs_notify_telegram "SKIPPED" \
    "Reason: ${reason}; solver executed: no; time: $(date -Is 2>/dev/null || date)"
}

pbs_notify_finish() {
  local rc="${1:-$?}"
  local end elapsed event host
  end="$(date +%s 2>/dev/null || echo 0)"
  elapsed=$((end - _PBS_NOTIFY_START_EPOCH))
  host="$(hostname 2>/dev/null || echo unknown)"
  if [ "${rc}" -eq 0 ]; then
    event="PASS"
  else
    event="FAIL"
  fi
  # Detect common abort signal exits
  if [ "${rc}" -eq 143 ] || [ "${rc}" -eq 137 ]; then
    event="ABORTED"
  fi
  pbs_notify_telegram "${event}" \
    "Exit: ${rc}; elapsed_seconds: ${elapsed}; host: ${host}; scratch: ${RUN_DIR:-unknown}"
  if [ "${PBS_NOTIFY_SKIP_EMAIL:-0}" != "1" ] && type pbs_mail_end >/dev/null 2>&1; then
    pbs_mail_end "${rc}" || true
  fi
  return "${rc}"
}

pbs_notify_install_traps() {
  # Preserve prior EXIT trap behavior by chaining
  trap 'rc=$?; pbs_notify_finish "$rc"; exit "$rc"' EXIT
  trap 'exit 143' TERM INT HUP
}
