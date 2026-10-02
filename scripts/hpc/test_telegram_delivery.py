#!/usr/bin/env python3
"""Safely test Telegram connectivity from mlogin01 without exposing secrets."""
import os
import subprocess
import sys
import json
from pathlib import Path

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import os, json, urllib.request, urllib.parse, sys
from pathlib import Path

config_path = Path.home() / ".config" / "adaptive-remeshing" / "notifications.json"
if not config_path.is_file():
    print(json.dumps({"error": "config_missing", "pass": False}))
    sys.exit(1)

config = json.loads(config_path.read_text())
bot_token = config.get("telegram_bot_token") or config.get("TELEGRAM_BOT_TOKEN")
chat_id = config.get("telegram_chat_id") or config.get("TELEGRAM_CHAT_ID")

if not bot_token or not chat_id:
    print(json.dumps({"error": "token_or_chat_id_missing", "pass": False}))
    sys.exit(1)

msg_text = \"\"\"[PRV_ADAPTIVE_REMESHING TEST]
Telegram notification connectivity test from mlogin01.
No PBS job was submitted.\"\"\"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": chat_id,
    "text": msg_text,
    "disable_web_page_preview": "true"
}).encode("utf-8")

req = urllib.request.Request(url, data=data, method="POST")

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        http_code = resp.getcode()
        body = json.loads(resp.read().decode("utf-8"))
        api_ok = body.get("ok") is True
        msg_id = body.get("result", {}).get("message_id")
        print(json.dumps({
            "http_status": http_code,
            "telegram_api_ok": api_ok,
            "message_id_present": msg_id is not None,
            "pass": (http_code == 200 and api_ok)
        }))
except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="replace")
    print(json.dumps({
        "http_status": e.code,
        "telegram_api_ok": False,
        "error": "http_error",
        "pass": False
    }))
except Exception as e:
    print(json.dumps({
        "telegram_api_ok": False,
        "error": str(e),
        "pass": False
    }))
"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        f"python3 -c {subprocess.list2cmdline([remote_script])}"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if res.returncode != 0:
        print("SSH Error:", res.stderr)
        sys.exit(1)
    
    print("TELEGRAM DELIVERY TEST RESULT:")
    print(res.stdout)

if __name__ == "__main__":
    main()
