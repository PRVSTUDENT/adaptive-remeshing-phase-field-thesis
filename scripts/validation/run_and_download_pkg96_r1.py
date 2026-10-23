#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_and_download_pkg96_r1.py
Uploads extract_pkg96_r1_results.py and run_pkg96_r1_extraction.sh.
Executes extraction on cluster and downloads audit artifacts.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package96_r1_c5_transfer"
local_dest = REPO_ROOT / "results/validation/mode1_f1597"

scripts_to_upload = [
    ("scripts/validation/extract_pkg96_r1_results.py", "extract_pkg96_r1_results.py"),
    ("scripts/validation/run_pkg96_r1_extraction.sh", "run_pkg96_r1_extraction.sh")
]

print("Uploading extraction scripts...")
for rel_src, dst_name in scripts_to_upload:
    src = str(REPO_ROOT / rel_src)
    dst = f"tu_freiberg:{rem_dir}/{dst_name}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed: {res.stderr}")
    print(f"Uploaded {dst_name} successfully.")

subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"chmod +x {rem_dir}/run_pkg96_r1_extraction.sh"], check=True)

rem_cmd = f"{rem_dir}/run_pkg96_r1_extraction.sh"
print(f"Executing extraction on cluster via {rem_cmd}...")
res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                      r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                      "-RemoteCommand", rem_cmd], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
if res.returncode != 0:
    print("STDERR:\n", res.stderr)
    raise RuntimeError(f"Extraction failed with exit code {res.returncode}")

out_files = [
    "pkg96_r1_solver_evaluation.json",
    "pkg96_r1_frame_history_summary.csv",
    "pkg96_r1_step4_terminal_nodal_state.csv",
    "uel_energy_balance.csv"
]

print("Downloading artifacts...")
for f in out_files:
    s = f"tu_freiberg:{rem_dir}/{f}"
    local_name = f if f != "uel_energy_balance.csv" else "pkg96_r1_uel_energy_balance.csv"
    d = str(local_dest / local_name)
    r = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", s, d], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"SCP failed for {f}: {r.stderr}")
    print(f"Downloaded {local_name} successfully.")

print("Package 96-R1 extraction and download completed.")
