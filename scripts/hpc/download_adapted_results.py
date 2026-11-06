# -*- coding: utf-8 -*-
"""Download extracted adapted simulation results from cluster to local repository."""
import subprocess
from pathlib import Path

files_to_download = [
    ("f1644_adapted_extracted_summary.json", "results/validation/f1644_adapted_extracted_summary.json"),
    ("f1644_adapted_localized_damage.csv", "results/validation/f1644_adapted_localized_damage.csv"),
    ("uel_energy_balance.csv", "results/validation/f1644_adapted_uel_energy_balance.csv"),
    ("pbs_execution.log", "results/validation/f1644_adapted_pbs_execution.log"),
    ("PK_HOLE_METHOD_A_ADAPT.sta", "results/validation/f1644_adapted_PK_HOLE_METHOD_A_ADAPT.sta"),
    ("PK_HOLE_METHOD_A_ADAPT.dat", "results/validation/f1644_adapted_PK_HOLE_METHOD_A_ADAPT.dat"),
    ("PK_HOLE_METHOD_A_ADAPT.msg", "results/validation/f1644_adapted_PK_HOLE_METHOD_A_ADAPT.msg")
]

remote_dir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_adapted"

for remote_name, local_dest in files_to_download:
    remote_path = f"{remote_dir}/{remote_name}"
    cmd = f"cat {remote_path}"
    ps_cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ]
    res = subprocess.run(ps_cmd, capture_output=True, text=True)
    if res.returncode == 0 and len(res.stdout.strip()) > 0:
        local_path = Path(local_dest)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(res.stdout, encoding="utf-8")
        print(f"Downloaded: {remote_name} -> {local_dest} ({len(res.stdout)} chars)")
    else:
        print(f"Note: {remote_name} not yet downloaded or empty: {res.stderr.strip()}")
