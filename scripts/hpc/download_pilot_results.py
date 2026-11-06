# -*- coding: utf-8 -*-
"""Download extracted pilot results from cluster to local repository."""
import subprocess
from pathlib import Path

files_to_download = [
    ("f1642_pilot_extracted_summary.json", "results/validation/f1642_pilot_extracted_summary.json"),
    ("uel_energy_balance.csv", "results/validation/f1642_pilot_uel_energy_balance.csv"),
    ("pbs_execution.log", "results/validation/f1642_pilot_pbs_execution.log"),
    ("PK_HOLE_METHOD_A_PROD.sta", "results/validation/f1642_pilot_PK_HOLE_METHOD_A_PROD.sta")
]

remote_dir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_pilot"

for remote_name, local_dest in files_to_download:
    remote_path = f"{remote_dir}/{remote_name}"
    cmd = f"cat {remote_path}"
    ps_cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ]
    res = subprocess.run(ps_cmd, capture_output=True, text=True)
    if res.returncode == 0:
        local_path = Path(local_dest)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(res.stdout, encoding="utf-8")
        print(f"Downloaded: {remote_name} -> {local_dest} ({len(res.stdout)} bytes)")
    else:
        print(f"Failed to download {remote_name}: {res.stderr}")
