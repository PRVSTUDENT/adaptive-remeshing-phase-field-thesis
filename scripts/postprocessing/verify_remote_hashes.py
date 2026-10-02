#!/usr/bin/env python3
"""Independently verify all 11 candidate hashes on remote cluster."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import hashlib, json, sys
from pathlib import Path

pkg_dir = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6")

expected = {
    "M2STATE_FRACFIX_RESTART1R1R6.inp": "304d7e0857a95e15ff3503639f74a789fc68b2cab9045a460a7c4f50b944dd80",
    "f42_mixed_uel.for": "be8138311b4ed4f199300e2ef87e1162bb6043b35c08f899cf623d955de834f0",
    "STATE_TRANSFER_ARTIFACT.json": "fea480f7859df21e34d6beef11674c94c780072f2e4606f4f4e336f569039e9c",
    "TRANSFER_MANIFEST.json": "87e569fa06e86412a5cb9c59dc80bda47d3916ce089d2552c32fd4e69cce30d2",
    "RESTART_ACCEPTANCE_CONTRACT.json": "c063ac7761b4ba650f0e58f5d3a1aeac789e72689865da161d7c26984f2e612f",
    "verify_restart_trace.py": "167c3b19deed67c553a4abd1364869b31cc69d5b8e8ddbfd7e98c757975885a6",
    "extract_restart1r1r6_odb.py": "60d7ef6a8022ab81f57d8a90145b4566a5bfc8a979f5ca0942832be32e7fc470",
    "verify_restart1r1r6_science.py": "d6c97ffd2f9a59165cf7224d09ff22ac999aca80b50a515e822deac53aaf7f3a",
    "M2STATE_FRACFIX_RESTART1R1R6.pbs": "124c21444856709dc35aa035e95110268f6137ba07c19ba2661bd9c94a18bf80",
    "submit_m2state_fracfix_restart1r1r6.sh": "d188b2e8dfb369a41d8933a377577ca402a03a2cf8ef228faa6d02261f0393a4",
    "PACKAGE_MANIFEST.json": "bfe8bef861c5e2f0612e1114b0e74695da9a4795cd59b3436e1261ec784bb42d"
}

all_match = True
for f_name, exp_hash in expected.items():
    p = pkg_dir / f_name
    if not p.is_file():
        print("MISSING: " + f_name)
        all_match = False
        continue
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual.lower() != exp_hash.lower():
        print("MISMATCH: " + f_name + " expected " + exp_hash + " got " + actual)
        all_match = False
    else:
        print("MATCH: " + f_name + " (" + actual[:16] + ")")

# Also verify PBS manifest preflight logic
manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
m = json.loads(manifest_path.read_text())
assert "files" in m, "Manifest missing 'files' key"
assert m.get("candidate") == "M2STATE_FRACFIX_RESTART1R1R6"

if not all_match:
    sys.exit(1)
print("EXACT REMOTE HASH CHECK: 100% PASS")
"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        f"python3 -c {subprocess.list2cmdline([remote_script])}"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    return res.returncode

if __name__ == "__main__":
    sys.exit(main())
