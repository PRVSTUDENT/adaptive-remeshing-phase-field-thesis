# Telegram HPC notification setup

## 1. Create the bot (user, in Telegram)

1. Open **@BotFather**.
2. `/newbot` → choose name and username.
3. Save the **HTTP API token** offline (password manager). Anyone with the token controls the bot.
4. Open your new bot and send **`/start`**.

Do **not** paste the token into ChatGPT, Git, PBS scripts, or `qsub -v`.

## 2. Store credentials on the HPC login node

SSH to the cluster, then:

```bash
cd ~/projects/adaptive-remeshing
bash scripts/hpc/telegram_setup_credentials.sh
```

This:

* creates `~/.config/hpc-notify/` (`700`)
* writes `telegram.env` (`600`) with the token (hidden input)
* discovers `TELEGRAM_CHAT_ID` via `getUpdates`
* runs a **login-node** `sendMessage` test

Manual alternative:

```bash
mkdir -p "$HOME/.config/hpc-notify"
chmod 700 "$HOME/.config/hpc-notify"
read -rsp "Telegram bot token: " TG_TOKEN; echo
printf 'TELEGRAM_BOT_TOKEN=%s\n' "$TG_TOKEN" > "$HOME/.config/hpc-notify/telegram.env"
unset TG_TOKEN
chmod 600 "$HOME/.config/hpc-notify/telegram.env"
python3 scripts/hpc/telegram_get_chat_id.py
# append TELEGRAM_CHAT_ID=... then chmod 600 again
```

## 3. Login-node test

```bash
python3 scripts/hpc/telegram_notify.py --strict \
  --event PASS \
  --job-id login-test \
  --job-name telegram_login_test \
  --message "Telegram login-node notification test"
```

You should receive a Telegram message. Exit code must be 0 with `--strict`.

## 4. Compute-node smoke test (non-scientific)

```bash
bash scripts/hpc/submit_telegram_smoke.sh
```

Expect: SUBMITTED (login) → BEGIN → PASS on Telegram.  
Record result in `runs/hpc/notifications/TELEGRAM_CONNECTIVITY_TEST.json`.

## 5. Security checklist

* [ ] `telegram.env` mode `600`
* [ ] not under the git tree / ignored by `.gitignore`
* [ ] token never in `qsub -v`, PBS scripts, or commits
* [ ] regenerate token via BotFather if exposed

## 6. Message events

```text
SUBMITTED → BEGIN → PASS | FAIL | SKIPPED | ABORTED
```

## References

* Telegram Bot Features / BotFather: https://core.telegram.org/bots/features  
* Bot API `sendMessage` / `getUpdates`: https://core.telegram.org/bots/api  
