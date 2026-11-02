# -*- coding: utf-8 -*-
"""
fetch_and_analyze_r8_telemetry.py
Fetch live iteration telemetry from cluster for Job 1419490.mmaster02 (Package 157-R8).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
"""

import json
from pathlib import Path
import subprocess

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"
REMOTE_FILE = "/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r8/continuation_1419490.mmaster02/live_iteration_telemetry.json"
LOCAL_FILE = REPO_ROOT / "results/validation/package157_r8_live_telemetry_turn30.json"


def fetch_r8():
    ps_cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(SSH_WRAPPER),
        "-RemoteCommand", f"cat {REMOTE_FILE}",
        "-TimeoutSeconds", "120"
    ]
    res = subprocess.run(ps_cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"R8 telemetry not yet ready or failed: {res.stderr}")
        return None
    raw = res.stdout.strip()
    idx_start = raw.find("[")
    idx_end = raw.rfind("]")
    if idx_start == -1 or idx_end == -1:
        print("No JSON array yet in R8 telemetry.")
        return None
    data = json.loads(raw[idx_start:idx_end + 1])
    LOCAL_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"R8 Telemetry: {len(data)} records, latest outer: {data[-1]['outer']}")
    print(f"Latest record keys: {list(data[-1].keys())}")
    print(f"Latest record: {json.dumps(data[-1], indent=2)}")
    return data


if __name__ == "__main__":
    fetch_r8()
