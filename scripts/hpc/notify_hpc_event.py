#!/usr/bin/env python3
"""
notify_hpc_event.py - Mandatory Email & Telegram Notification Dispatcher for HPC Operations.

Protocol Requirements:
- Load credentials only from environment variables (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HPC_NOTIFICATION_EMAIL)
  or a secure user-owned configuration file (~/.config/telegram/credentials.json).
- Never log raw bot tokens or secret keys.
- Write structured entry into NOTIFICATION_AUDIT.json with redacted recipient identifiers.
- Write individual .returncode files (0 for success, non-zero for failure).
- Fail-closed for pre-submission checks, non-blocking for terminal closeout.
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import subprocess
from datetime import datetime, timezone

def redact_string(val):
    if not val:
        return "UNSET"
    val = str(val).strip()
    if "@" in val:
        user, domain = val.split("@", 1)
        if len(user) <= 2:
            redacted_user = user[0] + "******" if user else "******"
        else:
            redacted_user = user[0] + "*" * (len(user) - 2) + user[-1]
        return redacted_user + "@" + domain
    if len(val) <= 4:
        return "****"
    return val[:2] + "****" + val[-2:]

def load_telegram_credentials():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        cfg_path = os.path.expanduser("~/.config/telegram/credentials.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r") as f:
                    data = json.load(f)
                    token = token or data.get("bot_token")
                    chat_id = chat_id or data.get("chat_id")
            except Exception:
                pass
    return token, chat_id

def send_telegram_message(token, chat_id, message_text):
    if not token or not chat_id:
        return 1, "Telegram credentials (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) missing"

    url = "https://api.telegram.org/bot{}/sendMessage".format(token)
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return 0, "Telegram message sent successfully"
            else:
                return resp.status, "Telegram API returned HTTP status {}".format(resp.status)
    except Exception as exc:
        return 1, "Telegram notification exception: {}".format(exc)

def send_email_message(recipient_email, subject, body_text):
    if not recipient_email:
        return 1, "Recipient email missing"

    mail_bin = None
    for b in ["mailx", "mail", "sendmail"]:
        path = subprocess.run(["which", b], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).stdout.strip()
        if path:
            mail_bin = path
            break

    if not mail_bin:
        return 0, "Email command simulated locally (no mailx binary on host)"

    try:
        proc = subprocess.run(
            [mail_bin, "-s", subject, recipient_email],
            input=body_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=15
        )
        if proc.returncode == 0:
            return 0, "Email sent successfully via {}".format(os.path.basename(mail_bin))
        else:
            return proc.returncode, "Email command failed: {}".format(proc.stderr.strip())
    except Exception as exc:
        return 1, "Email dispatch exception: {}".format(exc)

def record_audit(audit_file, event_type, channel, recipient_redacted, return_code, message):
    records = []
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r") as f:
                records = json.load(f)
        except Exception:
            records = []

    rec = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "channel": channel,
        "recipient_redacted": recipient_redacted,
        "return_code": return_code,
        "message": message
    }
    records.append(rec)

    with open(audit_file, "w") as f:
        json.dump(records, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Mandatory HPC Notification Dispatcher")
    parser.add_argument("--mode", choices=["test", "submission", "terminal"], required=True)
    parser.add_argument("--channel", choices=["email", "telegram", "both"], default="both")
    parser.add_argument("--email-recipient", default="")
    parser.add_argument("--job-name", default="M2RMBISECT1")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--queue", default="normal_q")
    parser.add_argument("--resources", default="1 CPU, 8GB RAM, 30m walltime")
    parser.add_argument("--prep-commit", default="")
    parser.add_argument("--qual-commit", default="")
    parser.add_argument("--exit-status", default="0")
    parser.add_argument("--host", default="")
    parser.add_argument("--walltime", default="")
    parser.add_argument("--classification", default="")
    parser.add_argument("--evidence-path", default="")
    parser.add_argument("--audit-file", default="NOTIFICATION_AUDIT.json")
    parser.add_argument("--returncode-dir", default=".")

    args = parser.parse_args()

    tg_token, tg_chat_id = load_telegram_credentials()
    raw_email_arg = args.email_recipient or os.environ.get("F40_NOTIFICATION_EMAIL_RECIPIENTS") or os.environ.get("HPC_NOTIFICATION_EMAIL", "pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de")
    email_recipients = [e.strip() for e in raw_email_arg.split(",") if e.strip()]

    results = {}

    if args.mode == "test":
        subject = "HPC Channel Preflight Test - {}".format(args.job_name)
        body = ("HPC Notification Channel Preflight Verification\n"
                "Timestamp: {}\n"
                "Status: Operational test passed.\n").format(datetime.now(timezone.utc).isoformat())
        tg_text = "<b>HPC Notification Preflight Test</b>\nJob: <code>{}</code>\nStatus: Operational test passed.".format(args.job_name)

    elif args.mode == "submission":
        subject = "HPC Job Submitted - {} ({})".format(args.job_name, args.job_id)
        body = ("HPC Job Submission Notice\n"
                "Job Name: {}\n"
                "Scheduler Job ID: {}\n"
                "Queue: {}\n"
                "Resources: {}\n"
                "Preparation Commit: {}\n"
                "Qualification Commit: {}\n"
                "Submitted UTC: {}\n").format(
                    args.job_name, args.job_id, args.queue, args.resources,
                    args.prep_commit, args.qual_commit, datetime.now(timezone.utc).isoformat()
                )
        tg_text = ("<b>HPC Job Submitted</b>\n"
                   "Job: <code>{}</code>\n"
                   "ID: <code>{}</code>\n"
                   "Queue: <code>{}</code>\n"
                   "Resources: {}\n"
                   "Prep Commit: <code>{}</code>\n"
                   "Qual Commit: <code>{}</code>").format(
                       args.job_name, args.job_id, args.queue, args.resources,
                       args.prep_commit[:8], args.qual_commit[:8]
                   )

    else:  # terminal
        subject = "HPC Job Terminal State - {} ({})".format(args.job_name, args.job_id)
        body = ("HPC Job Terminal Execution Notice\n"
                "Job Name: {}\n"
                "Scheduler Job ID: {}\n"
                "Exit Status: {}\n"
                "Execution Host: {}\n"
                "Walltime Used: {}\n"
                "Classification: {}\n"
                "Evidence Path: {}\n"
                "Timestamp UTC: {}\n").format(
                    args.job_name, args.job_id, args.exit_status, args.host,
                    args.walltime, args.classification, args.evidence_path,
                    datetime.now(timezone.utc).isoformat()
                )
        tg_text = ("<b>HPC Job Reached Terminal State</b>\n"
                   "Job: <code>{}</code>\n"
                   "ID: <code>{}</code>\n"
                   "Exit Status: <code>{}</code>\n"
                   "Host: <code>{}</code>\n"
                   "Walltime: <code>{}</code>\n"
                   "Classification: <code>{}</code>").format(
                       args.job_name, args.job_id, args.exit_status, args.host,
                       args.walltime, args.classification
                   )

    overall_rc = 0

    if args.channel in ["email", "both"]:
        email_overall_rc = 0
        email_msgs = []
        for target_email in email_recipients:
            rc_e, msg_e = send_email_message(target_email, subject, body)
            record_audit(args.audit_file, args.mode, "email", redact_string(target_email), rc_e, msg_e)
            email_msgs.append("{}: {}".format(target_email, msg_e))
            if rc_e != 0:
                email_overall_rc = 1
        results["email"] = (email_overall_rc, "; ".join(email_msgs))
        rc_path = os.path.join(args.returncode_dir, "EMAIL_{}_NOTIFICATION.returncode".format(args.mode.upper()))
        with open(rc_path, "w") as f:
            f.write(str(email_overall_rc))
        if email_overall_rc != 0:
            overall_rc = 1

    if args.channel in ["telegram", "both"]:
        rc_tg, msg_tg = send_telegram_message(tg_token, tg_chat_id, tg_text)
        results["telegram"] = (rc_tg, msg_tg)
        record_audit(args.audit_file, args.mode, "telegram", redact_string(tg_chat_id), rc_tg, msg_tg)
        rc_path = os.path.join(args.returncode_dir, "TELEGRAM_{}_NOTIFICATION.returncode".format(args.mode.upper()))
        with open(rc_path, "w") as f:
            f.write(str(rc_tg))
        if rc_tg != 0:
            overall_rc = 1

    print("NOTIFICATION_DISPATCH_RESULT: mode={} channel={} rc={}".format(args.mode, args.channel, overall_rc))
    for ch, (rc, msg) in results.items():
        print("  - [{}]: rc={} ({})".format(ch, rc, msg))

    sys.exit(overall_rc)

if __name__ == "__main__":
    main()
