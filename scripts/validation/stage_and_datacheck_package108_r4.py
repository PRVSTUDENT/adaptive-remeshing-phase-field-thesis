#!/usr/bin/env python3
"""
stage_and_datacheck_package108_r4.py
Stages Package 108 Revision 4 assets on the HPC cluster scratch and executes Abaqus 2023 datacheck.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    repo_root = Path("D:/Master thesis/Adaptive remeshing")
    ssh_cfg = Path.home() / ".ssh/codex_config"
    pkg_dir = repo_root / "models/pandey_kumar_mode1/108_r4_c3_staggered_continuation"
    rem_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r4"

    # 1. Create remote directory
    print(f"[Upload] Creating remote directory {rem_dir}...")
    create_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"mkdir -p {rem_dir}\""
    subprocess.run(create_cmd, shell=True, check=True)

    # 2. Write remote datacheck script with strictly Unix LF
    dc_script_path = pkg_dir / "run_pkg108_r4_datacheck.sh"
    dc_script_text = f"""#!/bin/bash
set -euo pipefail
cd {rem_dir}

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job=M1_C3_STAGGERED_R4 input=M1_C3_STAGGERED_R4_CONTINUATION.inp user=f42_experimental_irreversible_uel.for datacheck interactive
"""
    with open(dc_script_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(dc_script_text)

    # 3. Upload all package files
    files_to_upload = [
        "M1_C3_STAGGERED_R4_CONTINUATION.inp",
        "d_lower_bounds.csv",
        "f42_experimental_irreversible_uel.for",
        "submit_M1_C3_STAGGERED_R4.pbs",
        "job_notifications.sh",
        "M1_C3_STAGGERED_R4_AUTHORIZATION.json",
        "run_pkg108_r4_datacheck.sh"
    ]

    print(f"[Upload] Uploading {len(files_to_upload)} files via SCP...")
    for fname in files_to_upload:
        src = pkg_dir / fname
        dst = f"tu_freiberg:{rem_dir}/{fname}"
        res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src), dst], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"SCP failed for {fname}: {res.stderr}")
        print(f"  Uploaded {fname}")

    # 4. Make scripts executable and strip Windows CRLF
    strip_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"sed -i 's/\\r$//' {rem_dir}/*.sh {rem_dir}/*.pbs && chmod +x {rem_dir}/run_pkg108_r4_datacheck.sh {rem_dir}/job_notifications.sh {rem_dir}/submit_M1_C3_STAGGERED_R4.pbs\""
    subprocess.run(strip_cmd, shell=True, check=True)

    # 5. Execute datacheck on cluster
    print("[Datacheck] Running Abaqus 2023 datacheck on cluster...")
    dc_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"bash {rem_dir}/run_pkg108_r4_datacheck.sh\""
    res = subprocess.run(dc_cmd, shell=True, capture_output=True, text=True)
    print(f"Datacheck stdout:\n{res.stdout}")
    if res.returncode != 0:
        print(f"Datacheck stderr:\n{res.stderr}")
        raise RuntimeError(f"Datacheck failed with exit code {res.returncode}")

    # 6. Fetch datacheck .dat file back
    print("[Fetch] Downloading datacheck .dat file...")
    src_dat = f"tu_freiberg:{rem_dir}/M1_C3_STAGGERED_R4.dat"
    dst_dat = pkg_dir / "M1_C3_STAGGERED_R4.dat"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src_dat, str(dst_dat)], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to fetch .dat file: {res.stderr}")
    print(f"Successfully downloaded {dst_dat}")

if __name__ == "__main__":
    main()
