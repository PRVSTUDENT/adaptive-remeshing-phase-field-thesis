#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_package93.py
Upload Package 93 files to HPC cluster.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG93_DIR = REPO_ROOT / "models/pandey_kumar_mode1/93_c3_package93_instrumented_control"
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control"

files = [
    "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs",
    "run_pkg93_datacheck.sh",
    "PACKAGE_MANIFEST.json",
    "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY_AUTHORIZATION.json"
]

print(f"Uploading {len(files)} files to {rem_dir}...")
for f in files:
    src = str(PKG93_DIR / f)
    dst = f"tu_freiberg:{rem_dir}/{f}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {f}: {res.stderr}")
    print(f"Uploaded {f} successfully.")

print("All Package 93 files uploaded successfully.")
