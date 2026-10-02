#!/usr/bin/env python3
"""Safely inspect notification configuration on mlogin01 and local machine without exposing secrets."""
import os
import subprocess
import sys
import json
import stat
from pathlib import Path

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import os, stat, hashlib, json
from pathlib import Path

config_dir = Path.home() / ".config" / "adaptive-remeshing"
files_info = []

if config_dir.exists():
    for p in config_dir.iterdir():
        if p.is_file():
            st = os.stat(str(p))
            mode = oct(stat.S_IMODE(st.st_mode))
            content = p.read_text()
            keys = []
            tokens = {}
            if p.suffix == ".json" or content.strip().startswith("{"):
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        for k, v in data.items():
                            keys.append(k)
                            v_str = str(v)
                            tokens[k] = {
                                "present": True,
                                "nonempty": len(v_str) > 0,
                                "sha256_prefix": hashlib.sha256(v_str.encode()).hexdigest()[:8]
                            }
                except Exception as e:
                    pass
            else:
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        if k.startswith("export "):
                            k = k[7:].strip()
                        v = v.strip().strip("'").strip('"')
                        keys.append(k)
                        tokens[k] = {
                            "present": True,
                            "nonempty": len(v) > 0,
                            "sha256_prefix": hashlib.sha256(v.encode()).hexdigest()[:8]
                        }
            files_info.append({
                "path": str(p),
                "permissions": mode,
                "keys": keys,
                "token_info": tokens
            })

print(json.dumps(files_info, indent=2))
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
    
    print("REMOTE CONFIG CHECK RESULT:")
    print(res.stdout)

if __name__ == "__main__":
    main()
