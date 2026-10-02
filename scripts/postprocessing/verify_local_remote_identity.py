#!/usr/bin/env python3
import os
import subprocess
import json
import hashlib
import sys
from pathlib import Path

def main():
    local_dir = Path("models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6")
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")

    remote_cmd = """
import os, hashlib, json
hashes = {}
for f in sorted(os.listdir('.')):
    if os.path.isfile(f):
        hashes[f] = hashlib.sha256(open(f, 'rb').read()).hexdigest()
print(json.dumps(hashes))
"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        f"cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6 && python3 -c {subprocess.list2cmdline([remote_cmd])}"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if res.returncode != 0:
        print("SSH Error:", res.stderr)
        sys.exit(1)

    remote_hashes = json.loads(res.stdout.strip())

    all_match = True
    print("LOCAL vs REMOTE HASH COMPARISON:")
    print("=" * 100)
    for f in sorted(local_dir.iterdir()):
        if f.is_file():
            local_h = hashlib.sha256(f.read_bytes()).hexdigest()
            remote_h = remote_hashes.get(f.name, "MISSING")
            match = (local_h == remote_h)
            if not match:
                all_match = False
            print(f"{f.name:40s} | {local_h} | {'MATCH' if match else 'MISMATCH'}")
    print("=" * 100)
    print(f"final_restart_candidate_local_remote_identity = {all_match}")
    print(f"post_remote_qualification_hash_contract = {'PASS' if all_match else 'FAIL'}")

if __name__ == "__main__":
    main()
