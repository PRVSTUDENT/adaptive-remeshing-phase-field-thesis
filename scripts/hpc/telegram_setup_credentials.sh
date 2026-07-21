#!/bin/bash
# Interactive setup of private Telegram credentials on the HPC login node.
# Never echo the token. Does not write into the git repository.
set -euo pipefail

DIR="${HOME}/.config/hpc-notify"
FILE="${DIR}/telegram.env"

mkdir -p "${DIR}"
chmod 700 "${DIR}"

echo "Telegram HPC notification setup"
echo "Credential file: ${FILE}"
echo
echo "1) Create a bot with @BotFather (/newbot) if you have not already."
echo "2) Open the bot chat and send /start."
echo "3) Paste the bot token below (input is hidden)."
echo

read -rsp "Telegram bot token: " TG_TOKEN
echo
if [ -z "${TG_TOKEN}" ]; then
  echo "empty token" >&2
  exit 2
fi

umask 077
printf 'TELEGRAM_BOT_TOKEN=%s\n' "${TG_TOKEN}" > "${FILE}"
unset TG_TOKEN
chmod 600 "${FILE}"

echo "Token stored. Discovering chat ID via getUpdates..."
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHAT_LINE="$(python3 "${ROOT}/scripts/hpc/telegram_get_chat_id.py" 2>/tmp/tg_chat_err || true)"
if echo "${CHAT_LINE}" | grep -q '^TELEGRAM_CHAT_ID='; then
  CHAT_ID="$(echo "${CHAT_LINE}" | sed -n 's/^TELEGRAM_CHAT_ID=//p' | head -1)"
  echo "Discovered chat ID: ${CHAT_ID}"
  # drop existing CHAT_ID lines then append
  if grep -q '^TELEGRAM_CHAT_ID=' "${FILE}" 2>/dev/null; then
    grep -v '^TELEGRAM_CHAT_ID=' "${FILE}" > "${FILE}.tmp" || true
    mv "${FILE}.tmp" "${FILE}"
  fi
  printf 'TELEGRAM_CHAT_ID=%s\n' "${CHAT_ID}" >> "${FILE}"
  chmod 600 "${FILE}"
else
  echo "Could not auto-discover chat ID. Send /start to the bot, then run:"
  echo "  python3 ${ROOT}/scripts/hpc/telegram_get_chat_id.py"
  cat /tmp/tg_chat_err 2>/dev/null || true
  read -rp "Telegram chat ID (manual): " TG_CHAT_ID
  if [ -n "${TG_CHAT_ID}" ]; then
    printf 'TELEGRAM_CHAT_ID=%s\n' "${TG_CHAT_ID}" >> "${FILE}"
    unset TG_CHAT_ID
    chmod 600 "${FILE}"
  fi
fi

echo
echo "Keys present in credential file (values hidden):"
grep -E '^[A-Z_]+=' "${FILE}" | cut -d= -f1 || true
ls -la "${FILE}"

echo
echo "Running login-node connectivity test..."
python3 "${ROOT}/scripts/hpc/telegram_notify.py" --strict \
  --event PASS \
  --job-id login-test \
  --job-name telegram_login_test \
  --message "Telegram login-node notification test; time=$(date -Is 2>/dev/null || date)"

echo "setup_complete"
