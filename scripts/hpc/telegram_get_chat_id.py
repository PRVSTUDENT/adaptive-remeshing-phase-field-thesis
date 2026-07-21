#!/usr/bin/env python3
"""Discover Telegram private chat_id after the user sends /start to the bot.

Reads TELEGRAM_BOT_TOKEN from ~/.config/hpc-notify/telegram.env.
Never prints the token.
"""

from __future__ import print_function

import json
import os
import ssl
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError  # type: ignore

CRED_PATH = os.path.expanduser("~/.config/hpc-notify/telegram.env")
API_HOST = "api.telegram.org"
TIMEOUT_S = 15


def load_token(path):
    if not os.path.isfile(path):
        raise RuntimeError("missing %s — store TELEGRAM_BOT_TOKEN first" % path)
    token = None
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN=") or line.startswith("BOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not found in credentials file")
    return token


def get_updates(token):
    url = "https://%s/bot%s/getUpdates" % (API_HOST, token)
    req = Request(url)
    ctx = ssl.create_default_context()
    try:
        resp = urlopen(req, timeout=TIMEOUT_S, context=ctx)
        raw = resp.read()
    except TypeError:
        resp = urlopen(req, timeout=TIMEOUT_S)
        raw = resp.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    return json.loads(raw)


def main():
    try:
        token = load_token(CRED_PATH)
        data = get_updates(token)
    except Exception as exc:
        msg = str(exc)
        if "bot" in msg and ":" in msg:
            msg = "API request failed (token suppressed)"
        sys.stderr.write("ERROR: %s\n" % msg)
        return 2

    if not data.get("ok"):
        sys.stderr.write("ERROR: getUpdates failed: %s\n" % data.get("description", "unknown"))
        return 2

    results = data.get("result") or []
    if not results:
        sys.stderr.write(
            "ERROR: no updates found.\n"
            "Open your bot in Telegram, press Start or send /start, then re-run this script.\n"
        )
        return 3

    # Prefer most recent private chat
    chat_id = None
    username = None
    for upd in reversed(results):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("type") == "private" and "id" in chat:
            chat_id = chat["id"]
            username = chat.get("username") or chat.get("first_name")
            break
    if chat_id is None:
        # any chat
        for upd in reversed(results):
            msg = upd.get("message") or {}
            chat = msg.get("chat") or {}
            if "id" in chat:
                chat_id = chat["id"]
                username = chat.get("title") or chat.get("username")
                break

    if chat_id is None:
        sys.stderr.write("ERROR: could not extract chat id from updates\n")
        return 4

    print("TELEGRAM_CHAT_ID=%s" % chat_id)
    if username:
        print("# chat_label=%s" % username)
    print("# Append to ~/.config/hpc-notify/telegram.env then chmod 600")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
