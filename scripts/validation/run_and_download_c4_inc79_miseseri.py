#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_and_download_c4_inc79_miseseri.py
====================================
Uploads and executes C4 Increment-79 MISESERI extraction on cluster,
then downloads evidence to local package and validation directories.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 210)
"""
import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_c4_inc79_companion_miseseri"
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/114_c4_inc79_companion_miseseri"
val_dir = REPO_ROOT / "results/validation"

files = [
    ("scripts/validation/extract_c4_inc79_miseseri_distribution.py", "extract_c4_inc79_miseseri_distribution.py"),
    ("scripts/validation/run_c4_inc79_miseseri_extraction.sh", "run_c4_inc79_miseseri_extraction.sh")
]

def main():
    print("1. Uploading extraction scripts to cluster...")
    for src_rel, dst_name in files:
        src = str(REPO_ROOT / src_rel)
        dst = f"tu_freiberg:{rem_dir}/{dst_name}"
        res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"SCP failed for {dst_name}: {res.stderr}")
        print(f"   Uploaded: {dst_name}")

    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                    "-RemoteCommand", f"chmod +x {rem_dir}/run_c4_inc79_miseseri_extraction.sh"], check=True)

    print("2. Executing extraction on cluster...")
    res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                          r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                          "-RemoteCommand", f"bash {rem_dir}/run_c4_inc79_miseseri_extraction.sh"], capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    if res.returncode != 0:
        print("STDERR:\n", res.stderr)
        raise RuntimeError(f"Extraction failed with exit code {res.returncode}")

    print("3. Downloading extraction outputs...")
    for f in ["c4_inc79_miseseri_audit.json", "c4_inc79_companion_miseseri_distribution.csv"]:
        src_f = f"tu_freiberg:{rem_dir}/{f}"
        dst_pkg = str(pkg_dir / f)
        dst_val = str(val_dir / f)
        res1 = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src_f, dst_pkg], capture_output=True, text=True)
        res2 = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src_f, dst_val], capture_output=True, text=True)
        if res1.returncode != 0 or res2.returncode != 0:
            raise RuntimeError(f"SCP download failed for {f}")
        print(f"   Downloaded {f} successfully to package and validation directories.")

    # Also download solver log, sta, and msg
    for ext in ["sta", "msg", "dat"]:
        remote_file = f"tu_freiberg:{rem_dir}/M1_C4_INC79_COMPANION.{ext}"
        local_file = str(pkg_dir / f"M1_C4_INC79_COMPANION.{ext}")
        subprocess.run(["scp", "-F", str(ssh_cfg), "-B", remote_file, local_file], check=True)
        print(f"   Downloaded: M1_C4_INC79_COMPANION.{ext}")

    print("C4 Inc 79 MISESERI extraction and download completed successfully.")

if __name__ == "__main__":
    main()
