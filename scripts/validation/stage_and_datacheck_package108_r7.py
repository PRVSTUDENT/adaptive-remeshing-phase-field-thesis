#!/usr/bin/env python3
"""
stage_and_datacheck_package108_r7.py
Stages Package 108 Revision 7 assets on the HPC cluster scratch and executes Abaqus 2023 datacheck.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    repo_root = Path("D:/Master thesis/Adaptive remeshing")
    ssh_cfg = Path.home() / ".ssh/codex_config"
    pkg_dir = repo_root / "models/pandey_kumar_mode1/108_r7_c3_fixed_disp_am_cycles"
    rem_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r7"

    # 1. Create remote directory
    print(f"[Upload] Creating remote directory {rem_dir}...")
    create_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"mkdir -p {rem_dir}\""
    subprocess.run(create_cmd, shell=True, check=True)

    # 2. Write remote datacheck script with strictly Unix LF
    dc_script_path = pkg_dir / "run_pkg108_r7_datacheck.sh"
    dc_script_text = f"""#!/bin/bash
set -euo pipefail
cd {rem_dir}

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job=M1_C3_STAGGERED_R7 input=M1_C3_STAGGERED_R7_CONTINUATION.inp user=f42_experimental_irreversible_uel.for datacheck interactive
"""
    with open(dc_script_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(dc_script_text)

    # 3. SCP upload all required assets
    files_to_upload = [
        "M1_C3_STAGGERED_R7_CONTINUATION.inp",
        "f42_experimental_irreversible_uel.for",
        "d_lower_bounds.csv",
        "job_notifications.sh",
        "submit_M1_C3_STAGGERED_R7.pbs",
        "run_pkg108_r7_datacheck.sh"
    ]

    for fname in files_to_upload:
        fpath = pkg_dir / fname
        print(f"[Upload] Uploading {fname} via scp...")
        cmd_scp = ["scp", "-F", str(ssh_cfg), str(fpath), f"tu_freiberg:{rem_dir}/{fname}"]
        res = subprocess.run(cmd_scp, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"SCP failed for {fname}: {res.stderr}")

    # 4. Make scripts executable
    chmod_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"chmod +x {rem_dir}/*.sh\""
    subprocess.run(chmod_cmd, shell=True, check=True)

    # 5. Execute Datacheck on cluster
    print("[Datacheck] Executing Abaqus 2023 datacheck...")
    exec_dc_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"{rem_dir}/run_pkg108_r7_datacheck.sh\" -TimeoutSeconds 180"
    res_dc = subprocess.run(exec_dc_cmd, shell=True, capture_output=True, text=True)
    print(res_dc.stdout)
    if res_dc.stderr:
        print("[Stderr]", res_dc.stderr)

    # 6. Retrieve .dat and .sta files to verify datacheck status
    print("[Verification] Downloading .dat and .sta...")
    for ext in [".dat", ".sta", ".log"]:
        remote_file = f"{rem_dir}/M1_C3_STAGGERED_R7{ext}"
        local_file = pkg_dir / f"M1_C3_STAGGERED_R7{ext}"
        cmd_get = ["scp", "-F", str(ssh_cfg), f"tu_freiberg:{remote_file}", str(local_file)]
        subprocess.run(cmd_get, capture_output=True, text=True)

    dat_path = pkg_dir / "M1_C3_STAGGERED_R7.dat"
    if dat_path.exists():
        with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "CHECK RUN COMPLETE" in content or "NO ERRORS DETECTED" in content or "ANALYSIS DATACHECK COMPLETE" in content:
            print("[SUCCESS] Datacheck completed cleanly with 0 errors!")
        else:
            print("[WARNING] Could not confirm explicit datacheck completion string in .dat file.")
    else:
        print("[ERROR] .dat file was not found!")

if __name__ == "__main__":
    main()
