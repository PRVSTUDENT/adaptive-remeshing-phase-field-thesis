#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_package91.py
Upload Package 91 files to HPC cluster.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG91_DIR = REPO_ROOT / "models/pandey_kumar_mode1/91_c3_package91_instrumented_replay"
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package91_c3_instrumented_replay"

files = [
    "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "submit_M1_C3_PACKAGE91_INSTRUMENTED_REPLAY.pbs",
    "run_pkg91_datacheck.sh",
    "PACKAGE_MANIFEST.json",
    "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY_AUTHORIZATION.json"
]

print(f"Uploading {len(files)} files to {rem_dir}...")
for f in files:
    src = str(PKG91_DIR / f)
    dst = f"tu_freiberg:{rem_dir}/{f}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {f}: {res.stderr}")
    print(f"Uploaded {f} successfully.")

print("All Package 91 files uploaded successfully.")
