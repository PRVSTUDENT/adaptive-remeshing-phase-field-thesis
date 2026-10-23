#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_and_download_c4_miseseri.py
Uploads and executes C4 MISESERI extraction on cluster, then downloads evidence.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_c4_companion_miseseri"
loc_dir = REPO_ROOT / "results/validation/mode1_f1597"

files = [
    ("scripts/validation/extract_c4_miseseri_distribution.py", "extract_c4_miseseri_distribution.py"),
    ("scripts/validation/run_c4_miseseri_extraction.sh", "run_c4_miseseri_extraction.sh")
]

print("Uploading extraction scripts to cluster...")
for src_rel, dst_name in files:
    src = str(REPO_ROOT / src_rel)
    dst = f"tu_freiberg:{rem_dir}/{dst_name}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {dst_name}: {res.stderr}")

subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"chmod +x {rem_dir}/run_c4_miseseri_extraction.sh"], check=True)

print("Executing extraction on cluster...")
res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                      r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                      "-RemoteCommand", f"{rem_dir}/run_c4_miseseri_extraction.sh"], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
if res.returncode != 0:
    print("STDERR:\n", res.stderr)
    raise RuntimeError(f"Extraction failed with exit code {res.returncode}")

print("Downloading extraction outputs...")
for f in ["c4_miseseri_audit.json", "c4_companion_miseseri_distribution.csv"]:
    src_f = f"tu_freiberg:{rem_dir}/{f}"
    dst_f = str(loc_dir / f)
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src_f, dst_f], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP download failed for {f}: {res.stderr}")
    print(f"Downloaded {f} successfully.")

print("C4 MISESERI extraction and download completed successfully.")
