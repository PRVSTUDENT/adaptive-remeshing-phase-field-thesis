#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_file_ssh.py
Uploads a local file to the cluster via Invoke-GuardedSsh.ps1 in safe chunks.
"""

import os
import sys
import gzip
import base64
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def run_ssh(remote_cmd):
    cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(SSH_WRAPPER),
        "-RemoteCommand", remote_cmd
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("SSH command failed (code %d): %s\nStderr: %s" % 
                           (res.returncode, res.stdout, res.stderr))
    return res.stdout

def upload(local_path, remote_path, chunk_size=2000):
    local_p = Path(local_path)
    if not local_p.exists():
        raise RuntimeError("Local file not found: %s" % local_path)

    raw_data = local_p.read_bytes()
    compressed = gzip.compress(raw_data)
    b64 = base64.b64encode(compressed).decode("ascii")

    temp_remote = remote_path + ".tmp.b64"
    run_ssh("rm -f %s" % temp_remote)

    print("Uploading %s (%d bytes -> %d b64 chars) to %s..." % 
          (local_path, len(raw_data), len(b64), remote_path))

    for i in range(0, len(b64), chunk_size):
        chunk = b64[i:i+chunk_size]
        run_ssh("printf '%%s' '%s' >> %s" % (chunk, temp_remote))

    decode_cmd = ("python3 /scratch9/pr21vyci/runs/mode1_c3_companion_miseseri/remote_decode.py "
                  "%s %s" % (remote_path, temp_remote))
    out = run_ssh(decode_cmd)
    print(out.strip())
    run_ssh("rm -f %s" % temp_remote)

    # Verify remote hash
    remote_out = run_ssh("sha256sum %s" % remote_path)
    remote_hash = remote_out.strip().split()[0].upper()
    local_hash = sha256_file(local_p)

    if remote_hash != local_hash:
        raise RuntimeError("Hash mismatch! Local: %s, Remote: %s" % (local_hash, remote_hash))

    print("Upload verified: SHA256 %s" % remote_hash)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_file_ssh.py <local_path> <remote_path>")
        sys.exit(1)
    upload(sys.argv[1], sys.argv[2])
