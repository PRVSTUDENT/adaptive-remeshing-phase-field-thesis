#!/usr/bin/env python3
"""Write redacted notification evidence; secret values never enter output."""

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def fingerprint(value):
    return "redacted:" + hashlib.sha256(("f15-evidence:" + value).encode()).hexdigest()[:12]


def timestamps():
    now = datetime.now(timezone.utc)
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = "Europe/Berlin"
    if hasattr(time, "tzset"):
        time.tzset()
    local = datetime.fromtimestamp(now.timestamp()).astimezone().isoformat()
    if old_tz is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old_tz
    if hasattr(time, "tzset"):
        time.tzset()
    return now.isoformat().replace("+00:00", "Z"), local


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--channel", required=True, choices=("email", "telegram"))
    parser.add_argument("--recipient", required=True)
    parser.add_argument("--transport", required=True)
    parser.add_argument("--attempts", required=True, type=int)
    parser.add_argument("--command-status", required=True, type=int)
    parser.add_argument("--http-status", default="")
    parser.add_argument("--response-file")
    parser.add_argument("--message-id", default="")
    args = parser.parse_args()

    utc, local = timestamps()
    record = {
        "utc_timestamp": utc,
        "german_local_timestamp": local,
        "channel": args.channel,
        "recipient_fingerprint": fingerprint(args.recipient),
        "transport": args.transport,
        "attempt_count": args.attempts,
        "command_status": args.command_status,
        "pass": args.command_status == 0,
    }
    if args.channel == "telegram":
        response: dict[str, object] = {}
        try:
            response = json.loads(Path(args.response_file or "").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        ok = response.get("ok") is True
        message_id = response.get("result", {}).get("message_id") if isinstance(response.get("result"), dict) else None
        record.update(
            {
                "http_status": args.http_status,
                "telegram_ok": ok,
                "telegram_message_id": fingerprint(str(message_id)) if message_id is not None else None,
                "pass": args.command_status == 0 and args.http_status == "200" and ok,
            }
        )
    else:
        record["email_message_or_queue_id"] = args.message_id or None

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("pass=true" if record["pass"] else "pass=false")
    return 0 if record["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
