import subprocess
from pathlib import Path

repo_root = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r4"
pkg_dir = repo_root / "models/pandey_kumar_mode1/108_r4_c3_staggered_continuation"
res_dir = repo_root / "results/validation/mode1_f1597"

# 1. Upload script
src = repo_root / "scripts/validation/extract_mode1_turn127_r4_odb.py"
dst = f"tu_freiberg:{rem_dir}/extract_mode1_turn127_r4_odb.py"
subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src), dst], check=True)

# 2. Upload shell wrapper
sh_text = f"""#!/bin/bash
set -euo pipefail
cd {rem_dir}
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_mode1_turn127_r4_odb.py
"""
sh_path = repo_root / "scripts/validation/run_extract_r4.sh"
with open(sh_path, "w", newline="\n", encoding="utf-8") as f:
    f.write(sh_text)
subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(sh_path), f"tu_freiberg:{rem_dir}/run_extract_r4.sh"], check=True)

# 3. Run on cluster
cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"bash {rem_dir}/run_extract_r4.sh\""
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(res.stdout)
if res.returncode != 0:
    print(res.stderr)

# 4. Fetch deliverables
for fname in ["r4_extracted_telemetry.json", "uel_energy_balance.csv", "M1_C3_STAGGERED_R4.sta", "pbs_execution.log"]:
    src_f = f"tu_freiberg:{rem_dir}/{fname}"
    subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src_f, str(pkg_dir / fname)], check=True)
    if fname in ["r4_extracted_telemetry.json", "uel_energy_balance.csv"]:
        subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src_f, str(res_dir / fname)], check=True)
print("Downloaded all R4 deliverables successfully.")
