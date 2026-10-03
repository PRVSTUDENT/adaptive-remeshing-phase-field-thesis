#!/usr/bin/env bash
# Fail-closed Dual-Channel (Email + Telegram) Notification System for HPC PBS Workloads.
# Protocol Version: 1
# Maintainer: Gemini Antigravity

NOTIFICATION_MAX_ATTEMPTS="${NOTIFICATION_MAX_ATTEMPTS:-3}"
NOTIFICATION_RETRY_DELAY="${NOTIFICATION_RETRY_DELAY:-2}"
NOTIFICATION_START_EPOCH="${NOTIFICATION_START_EPOCH:-$(date +%s)}"
NOTIFICATION_START_UTC="${NOTIFICATION_START_UTC:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
NOTIFICATION_TERMINAL_SENT=0
NOTIFICATION_SIGNAL=""

# Find and resolve notification configuration deterministically
notification_resolve_config() {
  if [ -n "${NOTIFICATION_CONFIG:-}" ]; then
    if [ -f "$NOTIFICATION_CONFIG" ]; then
      echo "$NOTIFICATION_CONFIG"
      return 0
    else
      return 1
    fi
  fi
  local candidates=(
    "${HOME}/.config/adaptive-remeshing/notifications.env"
    "${HOME}/.config/adaptive-remeshing/notifications.json"
    "/home/pr21vyci/.config/adaptive-remeshing/notifications.env"
    "/home/pr21vyci/.config/adaptive-remeshing/notifications.json"
    "${HOME}/.notifications.env"
    "${HOME}/.notifications.json"
  )
  for c in "${candidates[@]}"; do
    if [ -f "$c" ]; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

notification_load_config() {
  local cfg
  cfg=$(notification_resolve_config) || {
    echo "[NOTIFICATION] ERROR: Notification configuration not found in environment or standard paths" >&2
    return 20
  }
  NOTIFICATION_CONFIG="$cfg"
  export NOTIFICATION_CONFIG

  # Check permissions: must not be world/group writable (mode <= 600)
  local perm
  perm=$(stat -c '%a' "$NOTIFICATION_CONFIG" 2>/dev/null || stat -f '%Lp' "$NOTIFICATION_CONFIG" 2>/dev/null || echo "600")
  if [ "$perm" != "600" ] && [ "$perm" != "400" ]; then
    echo "[NOTIFICATION] ERROR: Unsafe configuration file permissions ($perm); mode must be 600" >&2
    return 21
  fi

  if [[ "$NOTIFICATION_CONFIG" == *.json ]] || head -n 1 "$NOTIFICATION_CONFIG" | grep -q '^{' ; then
    # Parse JSON config safely using python3 without exposing secrets in logs
    local vars
    vars=$(python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    token = d.get("telegram_bot_token") or d.get("TELEGRAM_BOT_TOKEN", "")
    chat = d.get("telegram_chat_id") or d.get("TELEGRAM_CHAT_ID", "")
    email = d.get("email_recipients") or d.get("NOTIFY_EMAIL", "")
    if isinstance(email, list):
        email = email[0] if email else ""
    if not token or not chat:
        sys.exit(23)
    print(f"TELEGRAM_BOT_TOKEN={token}")
    print(f"TELEGRAM_CHAT_ID={chat}")
    print(f"NOTIFY_EMAIL={email}")
except Exception as e:
    sys.exit(22)
' "$NOTIFICATION_CONFIG" 2>/dev/null) || {
      echo "[NOTIFICATION] ERROR: Failed to parse JSON notification config or missing required keys" >&2
      return 22
    }
    eval "$vars"
  else
    # Sourcing standard shell env file
    # shellcheck disable=SC1090
    . "$NOTIFICATION_CONFIG"
  fi

  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "[NOTIFICATION] ERROR: TELEGRAM_BOT_TOKEN is missing or empty" >&2
    return 23
  fi
  if [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    echo "[NOTIFICATION] ERROR: TELEGRAM_CHAT_ID is missing or empty" >&2
    return 24
  fi
  if [ -z "${NOTIFY_EMAIL:-}" ]; then
    NOTIFY_EMAIL="pr21vyci@mailserver.tu-freiberg.de"
  fi

  export NOTIFY_EMAIL TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID
  return 0
}

notification_send_telegram_once() {
  local text="$1"
  local mock_mode="${NOTIFICATION_MOCK_TELEGRAM:-0}"
  if [ "$mock_mode" = "1" ]; then
    if [ "${NOTIFICATION_MOCK_FAIL:-0}" = "1" ]; then
      return 1
    fi
    return 0
  fi

  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    notification_load_config || return $?
  fi

  local resp_file http_code=0
  resp_file=$(mktemp)

  http_code=$(curl --silent --show-error --connect-timeout 10 --max-time 30 \
    --output "$resp_file" --write-out '%{http_code}' \
    --request POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${text}" \
    --data-urlencode "disable_web_page_preview=true" 2>/dev/null) || {
      rm -f "$resp_file"
      return 31
    }

  local api_ok=0
  if [ "$http_code" = "200" ]; then
    if python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("ok") is True else 1)' "$resp_file" 2>/dev/null; then
      api_ok=1
    fi
  fi

  rm -f "$resp_file"

  if [ "$http_code" = "200" ] && [ "$api_ok" -eq 1 ]; then
    return 0
  else
    echo "[NOTIFICATION] WARNING: Telegram API delivery failed (HTTP $http_code)" >&2
    return 32
  fi
}

notification_send_telegram() {
  local text="$1" attempt=1 max="${NOTIFICATION_MAX_ATTEMPTS:-3}" rc=0
  while [ "$attempt" -le "$max" ]; do
    notification_send_telegram_once "$text"
    rc=$?
    if [ "$rc" -eq 0 ]; then
      return 0
    fi
    [ "$attempt" -eq "$max" ] || sleep "${NOTIFICATION_RETRY_DELAY:-2}"
    attempt=$((attempt + 1))
  done
  return "$rc"
}

notification_send_email_once() {
  local subject="$1" body="$2"
  local sendmail_bin="${NOTIFICATION_SENDMAIL_BIN:-$(command -v sendmail 2>/dev/null || true)}"
  if [ -z "$sendmail_bin" ]; then
    return 0 # non-fatal if sendmail binary absent
  fi
  {
    printf 'To: %s\n' "${NOTIFY_EMAIL:-pr21vyci@mailserver.tu-freiberg.de}"
    printf 'Subject: %s\n' "$subject"
    printf 'Content-Type: text/plain; charset=UTF-8\n\n%s\n' "$body"
  } | "$sendmail_bin" -t >/dev/null 2>&1 || return $?
}

notification_send_email() {
  local subject="$1" body="$2"
  notification_send_email_once "$subject" "$body" || true
}

notify_submitted() {
  local job_id="$1" job_name="${2:-${CANDIDATE_NAME:-UNKNOWN}}" details="${3:-Submitted to PBS scheduler}"
  local queue="${PBS_QUEUE:-entry_imfdfkmq}" host
  host="$(hostname 2>/dev/null || echo "mlogin01")"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local msg
  msg="[PRV TEST - SUBMITTED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Queue: ${queue}
Host: ${host}
Timestamp: ${ts}
Details: ${details}"

  if [[ "${job_id}" != *"TEST"* ]] && [[ "${details}" != *"Synthetic"* ]]; then
    msg="[PRV_ADAPTIVE_REMESHING - SUBMITTED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Queue: ${queue}
Host: ${host}
Timestamp: ${ts}
Details: ${details}"
  fi

  notification_send_telegram "$msg"
}

notify_start() {
  local job_name="${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}"
  local job_id="${PBS_JOBID:-NOT_A_PBS_JOB}"
  local host queue ts
  host="$(hostname 2>/dev/null || echo "compute_node")"
  queue="${PBS_QUEUE:-entry_imfdfkmq}"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local msg
  msg="[PRV TEST - STARTED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Host: ${host}
Queue: ${queue}
Start Time: ${ts}"

  if [[ "${job_id}" != *"TEST"* ]] && [[ "${job_name}" != *"TEST"* ]]; then
    msg="[PRV_ADAPTIVE_REMESHING - STARTED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Host: ${host}
Queue: ${queue}
Start Time: ${ts}"
  fi

  notification_send_telegram "$msg" || true
  notification_send_email "START — ${job_name} — ${job_id}" "$msg"
}

notify_completed() {
  local job_name="${1:-${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}}"
  local job_id="${2:-${PBS_JOBID:-NOT_A_PBS_JOB}}"
  local elapsed="${3:-0}"
  local host ts
  host="$(hostname 2>/dev/null || echo "compute_node")"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local msg
  msg="[PRV TEST - COMPLETED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Host: ${host}
Exit Code: 0
Elapsed: ${elapsed}s
Timestamp: ${ts}"

  if [[ "${job_id}" != *"TEST"* ]] && [[ "${job_name}" != *"TEST"* ]]; then
    msg="[PRV_ADAPTIVE_REMESHING - COMPLETED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Host: ${host}
Exit Code: 0
Elapsed: ${elapsed}s
Timestamp: ${ts}"
  fi

  notification_send_telegram "$msg" || true
  notification_send_email "COMPLETED — ${job_name} — ${job_id}" "$msg"
}

notify_failed() {
  local job_name="${1:-${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}}"
  local job_id="${2:-${PBS_JOBID:-NOT_A_PBS_JOB}}"
  local rc="${3:-1}"
  local elapsed="${4:-0}"
  local host ts
  host="$(hostname 2>/dev/null || echo "compute_node")"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local msg="[PRV_ADAPTIVE_REMESHING - FAILED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Host: ${host}
Exit Code: ${rc}
Elapsed: ${elapsed}s
Timestamp: ${ts}"

  notification_send_telegram "$msg" || true
  notification_send_email "FAILED — ${job_name} — ${job_id} — RC=${rc}" "$msg"
}

notify_terminated() {
  local job_name="${1:-${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}}"
  local job_id="${2:-${PBS_JOBID:-NOT_A_PBS_JOB}}"
  local sig="${3:-TERM}"
  local elapsed="${4:-0}"
  local host ts
  host="$(hostname 2>/dev/null || echo "compute_node")"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local msg="[PRV_ADAPTIVE_REMESHING - TERMINATED]
Job Name: ${job_name}
PBS Job ID: ${job_id}
Host: ${host}
Termination Signal: ${sig}
Elapsed: ${elapsed}s
Timestamp: ${ts}"

  notification_send_telegram "$msg" || true
  notification_send_email "TERMINATED — ${job_name} — ${job_id} — SIG=${sig}" "$msg"
}

notify_terminal() {
  local rc="$1"
  local now end elapsed
  now=$(date +%s)
  elapsed=$((now - NOTIFICATION_START_EPOCH))
  local job_name="${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}"
  local job_id="${PBS_JOBID:-NOT_A_PBS_JOB}"

  if [ -n "$NOTIFICATION_SIGNAL" ]; then
    notify_terminated "$job_name" "$job_id" "$NOTIFICATION_SIGNAL" "$elapsed"
  elif [ "$rc" -eq 0 ]; then
    notify_completed "$job_name" "$job_id" "$elapsed"
  else
    notify_failed "$job_name" "$job_id" "$rc" "$elapsed"
  fi
}

notification_terminal_trap() {
  local rc="$1"
  if [ "$NOTIFICATION_TERMINAL_SENT" -eq 1 ]; then
    return "$rc"
  fi
  NOTIFICATION_TERMINAL_SENT=1
  trap - EXIT INT TERM HUP
  notify_terminal "$rc" || true
  return "$rc"
}

notification_signal_trap() {
  NOTIFICATION_SIGNAL="$1"
  case "$1" in
    INT) exit 130 ;;
    TERM) exit 143 ;;
    HUP) exit 129 ;;
    *) exit 1 ;;
  esac
}

notification_install_terminal_trap() {
  trap 'rc=$?; notification_terminal_trap "$rc"' EXIT
  trap 'notification_signal_trap INT' INT
  trap 'notification_signal_trap TERM' TERM
  trap 'notification_signal_trap HUP' HUP
}

notify_job_start() {
  local job_name="${1:-${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}}"
  local job_id="${2:-${PBS_JOBID:-NOT_A_PBS_JOB}}"
  local details="${3:-}"
  notify_start "$job_name"
}

notify_job_end() {
  local job_name="${1:-${PBS_JOBNAME:-${CANDIDATE_NAME:-UNKNOWN}}}"
  local job_id="${2:-${PBS_JOBID:-NOT_A_PBS_JOB}}"
  local rc="${3:-0}"
  local now end elapsed
  now=$(date +%s)
  elapsed=$((now - NOTIFICATION_START_EPOCH))
  if [ "$rc" -eq 0 ]; then
    notify_completed "$job_name" "$job_id" "$elapsed"
  else
    notify_failed "$job_name" "$job_id" "$rc" "$elapsed"
  fi
}

notify_event() {
  local event="$1"
  shift
  case "$event" in
    SUBMITTED|QUEUED)
      notify_submitted "$@"
      ;;
    STARTED|START)
      notify_start "$@"
      ;;
    COMPLETED)
      notify_completed "$@"
      ;;
    FAILED)
      notify_failed "$@"
      ;;
    TERMINATED)
      notify_terminated "$@"
      ;;
    *)
      notification_send_telegram "[PRV_ADAPTIVE_REMESHING] Event: $event $*" || true
      ;;
  esac
}
