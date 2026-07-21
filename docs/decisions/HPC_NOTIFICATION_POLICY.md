# HPC Notification Policy

**Status:** active  
**Primary channel:** Telegram Bot API (`sendMessage`)  
**Secondary channel:** PBS email (`#PBS -m abe` + student address)  
**Date:** 2026-07-21

## Policy

```text
Telegram: primary operational notification
PBS email: secondary best-effort fallback
Notification failure must never fail scientific execution
No secrets in repository
No secrets through qsub -v / PBS metadata
```

## Events

| Event | When | Source |
| --- | --- | --- |
| SUBMITTED | immediately after successful `qsub` | login-node wrapper |
| BEGIN | job starts on compute node | PBS script trap |
| PASS | exit code 0 | PBS EXIT trap |
| FAIL | nonzero scientific/technical exit | PBS EXIT trap |
| SKIPPED | marker missing; no solver work | PBS script branch |
| ABORTED | signal exits (e.g. 143) where detectable | PBS EXIT trap |

## Credentials (private)

| Item | Location |
| --- | --- |
| Directory | `~/.config/hpc-notify/` mode `700` |
| File | `~/.config/hpc-notify/telegram.env` mode `600` |
| Keys | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |

Never commit `telegram.env`. Never print the token. Never put the token in PBS scripts or `qsub -v`.

## Scripts

| Script | Role |
| --- | --- |
| `scripts/hpc/telegram_setup_credentials.sh` | interactive token/chat setup on login node |
| `scripts/hpc/telegram_get_chat_id.py` | `getUpdates` → chat ID |
| `scripts/hpc/telegram_notify.py` | `sendMessage` client |
| `scripts/hpc/pbs_notify.sh` | BEGIN/PASS/FAIL/SKIPPED helpers for PBS |
| `scripts/hpc/pbs_job_mail_notify.sh` | optional email secondary |
| `scripts/hpc/stage_c2/13_telegram_smoke.pbs` | non-Abaqus compute HTTPS smoke |

## Email secondary

Keep:

```text
#PBS -m abe
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de
```

Record whether PBS system mail, mailx fallback, Telegram, or combinations arrive, to understand duplicates. Once Telegram is verified, set `PBS_NOTIFY_SKIP_EMAIL=1` in jobs if duplicate mail is unwanted.

## Fallback if compute nodes block HTTPS

1. Keep SUBMITTED on the login node.  
2. Jobs still write markers/status JSON.  
3. Optional login-side watcher polls `qstat -x` / status files and sends BEGIN/PASS/FAIL.  
4. No inbound webhooks on the cluster.

## Scientific gate independence

Telegram/email delivery problems must not change Abaqus exit codes, markers, or Stage C scientific classification.
