# Source from PBS job scripts (login/compute) for reliable begin/end mail.
# PBS -m abe is still required; this is a belt-and-braces fallback when the
# site MTA does not deliver cluster system mail to the user's inbox.
#
# Usage (near top of PBS script, after set):
#   # shellcheck source=/dev/null
#   source "${PBS_O_WORKDIR:-.}/scripts/hpc/pbs_job_mail_notify.sh" 2>/dev/null \
#     || source "/home/pr21vyci/projects/adaptive-remeshing/scripts/hpc/pbs_job_mail_notify.sh" 2>/dev/null \
#     || true
#   pbs_mail_begin
#   trap 'pbs_mail_end $?' EXIT

# Default recipients: university student inbox first, cluster mailbox second.
PBS_NOTIFY_EMAILS="${PBS_NOTIFY_EMAILS:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de}"

_pbs_mail_send() {
  local subject="$1"
  local body="$2"
  local to
  # Prefer mailx; fall back to mail / sendmail-compatible mail
  for to in $(echo "${PBS_NOTIFY_EMAILS}" | tr ',' ' '); do
    [ -n "${to}" ] || continue
    if command -v mailx >/dev/null 2>&1; then
      printf '%s\n' "${body}" | mailx -s "${subject}" "${to}" 2>/dev/null || true
    elif command -v mail >/dev/null 2>&1; then
      printf '%s\n' "${body}" | mail -s "${subject}" "${to}" 2>/dev/null || true
    fi
  done
}

pbs_mail_begin() {
  local host
  host="$(hostname 2>/dev/null || echo unknown)"
  _pbs_mail_send \
    "PBS BEGIN ${PBS_JOBNAME:-job} ${PBS_JOBID:-unknown}" \
    "PBS job started
Job name: ${PBS_JOBNAME:-unset}
Job ID:   ${PBS_JOBID:-unset}
Host:     ${host}
User:     ${USER:-unset}
Queue:    ${PBS_QUEUE:-unset}
Workdir:  ${PBS_O_WORKDIR:-unset}
Time:     $(date -Is 2>/dev/null || date)
"
}

pbs_mail_end() {
  local rc="${1:-$?}"
  local host
  host="$(hostname 2>/dev/null || echo unknown)"
  _pbs_mail_send \
    "PBS END rc=${rc} ${PBS_JOBNAME:-job} ${PBS_JOBID:-unknown}" \
    "PBS job finished
Job name: ${PBS_JOBNAME:-unset}
Job ID:   ${PBS_JOBID:-unset}
Exit/rc:  ${rc}
Host:     ${host}
User:     ${USER:-unset}
Time:     $(date -Is 2>/dev/null || date)
"
}
