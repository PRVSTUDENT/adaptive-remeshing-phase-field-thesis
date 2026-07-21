#!/usr/bin/env python3
"""Send Telegram notifications for HPC jobs (primary channel).

Credentials are read only from the private file:
  ~/.config/hpc-notify/telegram.env

Never print the bot token or full API URL. Notification failures warn to
stderr and exit 0 by default so scientific jobs are never failed by Telegram.
Use --strict only for connectivity tests.
"""

from __future__ import print_function

import argparse
import json
import os
import ssl
import sys

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
except ImportError:  # Python 2
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urllib import urlencode  # type: ignore

CRED_PATH = os.path.expanduser("~/.config/hpc-notify/telegram.env")
API_HOST = "api.telegram.org"
MAX_LEN = 4000
TIMEOUT_S = 15


def load_env(path):
    data = {}
    if not os.path.isfile(path):
        raise RuntimeError(
            "missing credentials file: %s (see docs/guides/TELEGRAM_HPC_NOTIFICATION_SETUP.md)"
            % path
        )
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    token = data.get("TELEGRAM_BOT_TOKEN") or data.get("BOT_TOKEN")
    chat = data.get("TELEGRAM_CHAT_ID") or data.get("CHAT_ID")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in credentials file")
    if not chat:
        raise RuntimeError("TELEGRAM_CHAT_ID not set in credentials file")
    return token, chat


def api_post(token, method, fields):
    # Build URL without logging token
    url = "https://%s/bot%s/%s" % (API_HOST, token, method)
    body = urlencode(fields).encode("utf-8")
    req = Request(url, data=body)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    ctx = ssl.create_default_context()
    try:
        resp = urlopen(req, timeout=TIMEOUT_S, context=ctx)
        raw = resp.read()
    except TypeError:
        # older Python without context=
        resp = urlopen(req, timeout=TIMEOUT_S)
        raw = resp.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    return json.loads(raw)


def format_message(event, job_id, job_name, message):
    lines = [
        "[%s] Abaqus HPC job" % event,
        "Job: %s" % (job_id or "unknown"),
        "Name: %s" % (job_name or "unknown"),
    ]
    if message:
        for part in str(message).split(";"):
            p = part.strip()
            if p:
                lines.append(p)
    text = "\n".join(lines)
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 20] + "\n...[truncated]"
    return text


def send_message(token, chat_id, text):
    return api_post(
        token,
        "sendMessage",
        {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": "true",
        },
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--event",
        required=True,
        choices=["SUBMITTED", "BEGIN", "PASS", "FAIL", "SKIPPED", "ABORTED"],
    )
    ap.add_argument("--job-id", default="unknown")
    ap.add_argument("--job-name", default="unknown")
    ap.add_argument("--message", default="")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="nonzero exit on delivery failure (connectivity tests only)",
    )
    ap.add_argument(
        "--cred-file",
        default=CRED_PATH,
        help="override credentials path (default: ~/.config/hpc-notify/telegram.env)",
    )
    args = ap.parse_args(argv)

    try:
        token, chat_id = load_env(args.cred_file)
        text = format_message(args.event, args.job_id, args.job_name, args.message)
        result = send_message(token, chat_id, text)
        if not result.get("ok"):
            raise RuntimeError("Telegram API ok=false: %s" % result.get("description", "unknown"))
        # Success: no secrets
        print("telegram_ok event=%s job=%s" % (args.event, args.job_id))
        return 0
    except Exception as exc:
        # Never print token
        msg = str(exc)
        if "bot" in msg and ":" in msg:
            msg = "telegram delivery failed (details suppressed)"
        sys.stderr.write("WARNING: telegram_notify: %s\n" % msg)
        return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
