#!/usr/bin/env bash
# Fail-closed Pre-Submission Notification Verification Gate
# Verifies notification config, permissions, and helper readiness before qsub is permitted.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "./job_notifications.sh" ]; then
  echo "[PREFLIGHT ERROR] job_notifications.sh missing in $SCRIPT_DIR" >&2
  exit 1
fi

# shellcheck disable=SC1091
source ./job_notifications.sh

# 1. Resolve configuration
CFG=$(notification_resolve_config) || {
  echo "[PREFLIGHT ERROR] Could not resolve notification config file" >&2
  exit 2
}

# 2. Check permissions (must be 600 or 400)
PERM=$(stat -c '%a' "$CFG" 2>/dev/null || stat -f '%Lp' "$CFG" 2>/dev/null || echo "000")
if [ "$PERM" != "600" ] && [ "$PERM" != "400" ]; then
  echo "[PREFLIGHT ERROR] Unsafe config permissions ($PERM) on $CFG; must be 600 or 400" >&2
  exit 3
fi

# 3. Load config and check required variables
notification_load_config || {
  echo "[PREFLIGHT ERROR] notification_load_config failed" >&2
  exit 4
}

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "[PREFLIGHT ERROR] TELEGRAM_BOT_TOKEN is empty" >&2
  exit 5
fi

if [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "[PREFLIGHT ERROR] TELEGRAM_CHAT_ID is empty" >&2
  exit 6
fi

# 4. Verify helper functions exist and are executable
for fn in notification_load_config notification_send_telegram notify_submitted notify_start notify_completed notify_failed notification_install_terminal_trap; do
  if ! declare -f "$fn" >/dev/null; then
    echo "[PREFLIGHT ERROR] Required helper function $fn is not defined" >&2
    exit 7
  fi
done

echo "[PREFLIGHT SUCCESS] Notification pre-submission gate passed: configuration valid, mode $PERM, all helpers verified."
exit 0
