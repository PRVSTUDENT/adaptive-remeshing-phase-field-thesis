#!/usr/bin/env bash
# Shared fail-closed email + Telegram notifications for PBS workloads.

NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_MAX_ATTEMPTS="${NOTIFICATION_MAX_ATTEMPTS:-3}"
NOTIFICATION_RETRY_DELAY="${NOTIFICATION_RETRY_DELAY:-5}"
NOTIFICATION_EVIDENCE_DIR="${NOTIFICATION_EVIDENCE_DIR:-${PBS_O_WORKDIR:-$PWD}/notification_evidence}"
NOTIFICATION_HELPER="${NOTIFICATION_HELPER:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/notification_evidence.py}"
NOTIFICATION_START_EPOCH="${NOTIFICATION_START_EPOCH:-$(date +%s)}"
NOTIFICATION_START_UTC="${NOTIFICATION_START_UTC:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
NOTIFICATION_TERMINAL_SENT=0
NOTIFICATION_SIGNAL=""

notification_load_config() {
  [ -f "$NOTIFICATION_CONFIG" ] || { echo "notification config missing" >&2; return 20; }
  [ "$(stat -c '%a' "$NOTIFICATION_CONFIG")" = 600 ] || { echo "notification config permissions must be 600" >&2; return 21; }
  # shellcheck disable=SC1090
  . "$NOTIFICATION_CONFIG"
  [ -n "${NOTIFY_EMAIL:-}" ] || { echo "NOTIFY_EMAIL missing" >&2; return 22; }
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] || { echo "TELEGRAM_BOT_TOKEN missing" >&2; return 23; }
  [ -n "${TELEGRAM_CHAT_ID:-}" ] || { echo "TELEGRAM_CHAT_ID missing" >&2; return 24; }
  case "$NOTIFY_EMAIL" in *$'\r'*|*$'\n'*) echo "invalid email value" >&2; return 25;; esac
  export NOTIFY_EMAIL TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID
}

notification_retry() {
  local attempt=1 rc=1 max="$NOTIFICATION_MAX_ATTEMPTS"
  [ "$max" -ge 1 ] 2>/dev/null || max=1
  [ "$max" -le 3 ] || max=3
  while [ "$attempt" -le "$max" ]; do
    "$@" && { NOTIFICATION_LAST_ATTEMPTS="$attempt"; export NOTIFICATION_LAST_ATTEMPTS; return 0; }
    rc=$?
    [ "$attempt" -eq "$max" ] || sleep "$NOTIFICATION_RETRY_DELAY"
    attempt=$((attempt + 1))
  done
  NOTIFICATION_LAST_ATTEMPTS="$max"; export NOTIFICATION_LAST_ATTEMPTS
  return "$rc"
}

notification_email_once() {
  local subject="$1" body="$2" output="$3"
  local sendmail_bin="${NOTIFICATION_SENDMAIL_BIN:-$(command -v sendmail 2>/dev/null || true)}"
  [ -n "$sendmail_bin" ] || return 30
  { printf 'To: %s\n' "$NOTIFY_EMAIL"; printf 'Subject: %s\n' "$subject"; printf 'Content-Type: text/plain; charset=UTF-8\n\n%s\n' "$body"; } |
    "$sendmail_bin" -t >"$output" 2>&1
}

notify_email() {
  local event="$1" text="$2" evidence="$3" raw rc=0 msg_id=""
  raw=$(mktemp)
  notification_retry notification_email_once "$event" "$text" "$raw" || rc=$?
  msg_id=$(grep -Eio '(message[- ]id|queue[- ]id)[:= ][^[:space:]]+' "$raw" | head -n1 | sed 's/.*[:= ]//' || true)
  python3 "$NOTIFICATION_HELPER" --output "$evidence" --channel email --recipient "$NOTIFY_EMAIL" \
    --transport sendmail --attempts "${NOTIFICATION_LAST_ATTEMPTS:-1}" --command-status "$rc" --message-id "$msg_id" >/dev/null || rc=1
  rm -f "$raw"
  return "$rc"
}

notification_telegram_once() {
  local text="$1" response="$2" status_file="$3" status
  status=$(curl --silent --show-error --output "$response" --write-out '%{http_code}' \
    --request POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=${text}" \
    --data-urlencode 'disable_web_page_preview=true') || return $?
  printf '%s' "$status" >"$status_file"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); raise SystemExit(0 if d.get("ok") is True else 1)' "$response"
}

notify_telegram() {
  local event="$1" text="$2" evidence="$3" response status_file rc=0 http_status
  response=$(mktemp); status_file=$(mktemp)
  notification_retry notification_telegram_once "$text" "$response" "$status_file" || rc=$?
  http_status=$(cat "$status_file" 2>/dev/null || true)
  python3 "$NOTIFICATION_HELPER" --output "$evidence" --channel telegram --recipient "$TELEGRAM_CHAT_ID" \
    --transport curl_https_post --attempts "${NOTIFICATION_LAST_ATTEMPTS:-1}" --command-status "$rc" \
    --http-status "$http_status" --response-file "$response" >/dev/null || rc=1
  rm -f "$response" "$status_file"
  return "$rc"
}

notification_context() {
  printf 'Project: Adaptive remeshing\nStage: %s\nPBS job name: %s\nPBS job ID: %s\nQueue: %s\nExecution host: %s\nUTC timestamp: %s\nGerman local timestamp: %s\nRun ID: %s\nEvent: %s\nEvidence directory: %s' \
    "${NOTIFICATION_STAGE:-F15}" "${PBS_JOBNAME:-NOT_A_PBS_JOB}" "${PBS_JOBID:-NOT_A_PBS_JOB}" \
    "${PBS_QUEUE:-NOT_A_PBS_JOB}" "$(hostname)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$(TZ=Europe/Berlin date +%Y-%m-%dT%H:%M:%S%:z)" "${NOTIFICATION_RUN_ID:-direct-test}" "$1" "$NOTIFICATION_EVIDENCE_DIR"
}

notify_all() {
  local event="$1" text="$2" prefix="$3" email_rc=0 telegram_rc=0
  mkdir -p "$NOTIFICATION_EVIDENCE_DIR"
  if [ "${NOTIFICATION_EMAIL_MODE:-custom}" != native_pbs ]; then
    notify_email "$event" "$text" "$NOTIFICATION_EVIDENCE_DIR/${prefix}_EMAIL.json" || email_rc=$?
  fi
  notify_telegram "$event" "$text" "$NOTIFICATION_EVIDENCE_DIR/${prefix}_TELEGRAM.json" || telegram_rc=$?
  [ "$email_rc" -eq 0 ] && [ "$telegram_rc" -eq 0 ]
}

notify_start() {
  local context
  context=$(notification_context START)
  notify_all "START — ${PBS_JOBNAME:-NOT_A_PBS_JOB} — ${PBS_JOBID:-NOT_A_PBS_JOB}" "$context" NOTIFICATION_START
}

notify_terminal() {
  local rc="$1" classification="COMPLETED" end elapsed context
  [ "$rc" -eq 0 ] || classification="FAILED"
  [ -z "$NOTIFICATION_SIGNAL" ] || classification="TERMINATED"
  end=$(date +%s); elapsed=$((end - NOTIFICATION_START_EPOCH))
  context="$(notification_context "$classification")
Exit code: $rc
Classification: $classification
Start time: $NOTIFICATION_START_UTC
End time: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Elapsed seconds: $elapsed
Stdout path: ${NOTIFICATION_STDOUT_PATH:-unknown}
Stderr path: ${NOTIFICATION_STDERR_PATH:-unknown}"
  notify_all "$classification — ${PBS_JOBNAME:-NOT_A_PBS_JOB} — ${PBS_JOBID:-NOT_A_PBS_JOB} — RC=$rc" "$context" NOTIFICATION_TERMINAL
}

notification_terminal_trap() {
  local rc="$1"
  [ "$NOTIFICATION_TERMINAL_SENT" -eq 0 ] || return "$rc"
  NOTIFICATION_TERMINAL_SENT=1
  trap - EXIT INT TERM HUP
  notify_terminal "$rc" || true
  return "$rc"
}

notification_signal_trap() {
  NOTIFICATION_SIGNAL="$1"
  case "$1" in INT) exit 130;; TERM) exit 143;; HUP) exit 129;; esac
}

notification_install_terminal_trap() {
  trap 'rc=$?; notification_terminal_trap "$rc"; exit "$rc"' EXIT
  trap 'notification_signal_trap INT' INT
  trap 'notification_signal_trap TERM' TERM
  trap 'notification_signal_trap HUP' HUP
}
