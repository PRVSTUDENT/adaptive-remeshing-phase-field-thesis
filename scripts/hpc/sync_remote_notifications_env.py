#!/usr/bin/env python3
"""Safely ensure ~/.config/adaptive-remeshing/notifications.env exists with mode 600 from notifications.json."""
import os
import subprocess
import sys
from pathlib import Path

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import os, json, stat
from pathlib import Path

config_dir = Path.home() / ".config" / "adaptive-remeshing"
json_path = config_dir / "notifications.json"
env_path = config_dir / "notifications.env"

if json_path.is_file():
    data = json.loads(json_path.read_text())
    bot_token = data.get("telegram_bot_token") or data.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = data.get("telegram_chat_id") or data.get("TELEGRAM_CHAT_ID", "")
    emails = data.get("email_recipients") or data.get("NOTIFY_EMAIL", "")
    if isinstance(emails, list):
        email_str = emails[0] if len(emails) > 0 else "pr21vyci@mailserver.tu-freiberg.de"
    else:
        email_str = str(emails) if emails else "pr21vyci@mailserver.tu-freiberg.de"
    
    # Write notifications.env
    env_content = f'''# Adaptive Remeshing HPC Notification Configuration
NOTIFY_EMAIL="{email_str}"
TELEGRAM_BOT_TOKEN="{bot_token}"
TELEGRAM_CHAT_ID="{chat_id}"
export NOTIFY_EMAIL TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID
'''
    # Create or update with 600 permissions
    if env_path.exists():
        env_path.unlink()
    
    # Use os.open with O_CREAT | O_WRONLY, 0o600 to ensure file is created with 600 mode
    fd = os.open(str(env_path), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(env_content)
    
    os.chmod(str(env_path), 0o600)
    st = os.stat(str(env_path))
    mode = oct(stat.S_IMODE(st.st_mode))
    print(f"CREATED: {env_path} (mode {mode})")
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
    
    print("RESULT:")
    print(res.stdout)

if __name__ == "__main__":
    main()
