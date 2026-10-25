#!/usr/bin/env python3
"""
run_r3_extraction.py
Uploads extract_mode1_turn126_r3_odb.py, runs Abaqus python extraction on cluster,
and downloads r3_extracted_telemetry.json and uel_energy_balance.csv.
"""

import subprocess
from pathlib import Path

def main():
    repo_root = Path("D:/Master thesis/Adaptive remeshing")
    ssh_cfg = Path.home() / ".ssh/codex_config"
    rem_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r3"
    pkg_dir = repo_root / "models/pandey_kumar_mode1/108_r3_c3_staggered_continuation"
    res_dir = repo_root / "results/validation/mode1_f1597"
    res_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write and upload extraction wrapper
    sh_text = f"""#!/bin/bash
set -euo pipefail
cd {rem_dir}
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_mode1_turn126_r3_odb.py
"""
    sh_path = pkg_dir / "run_r3_extract.sh"
    with open(sh_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(sh_text)

    src_ext = repo_root / "scripts/validation/extract_mode1_turn126_r3_odb.py"
    dst_ext = f"tu_freiberg:{rem_dir}/extract_mode1_turn126_r3_odb.py"
    subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src_ext), dst_ext], check=True)
    subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(sh_path), f"tu_freiberg:{rem_dir}/run_r3_extract.sh"], check=True)
    print("Uploaded extraction scripts.")

    # 2. Run extraction wrapper on cluster
    cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"bash {rem_dir}/run_r3_extract.sh\""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Extraction stdout:\n{res.stdout}")
    if res.returncode != 0:
        print(f"Extraction stderr:\n{res.stderr}")
        raise RuntimeError("Extraction failed on cluster")

    # 3. Download results
    for fname in ["r3_extracted_telemetry.json", "uel_energy_balance.csv", "M1_C3_STAGGERED_R3.sta", "pbs_execution.log"]:
        src = f"tu_freiberg:{rem_dir}/{fname}"
        dst_pkg = pkg_dir / fname
        subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, str(dst_pkg)], check=True)
        if fname in ["r3_extracted_telemetry.json", "uel_energy_balance.csv"]:
            dst_res = res_dir / fname
            subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, str(dst_res)], check=True)
        print(f"Downloaded {fname}")

if __name__ == "__main__":
    main()
