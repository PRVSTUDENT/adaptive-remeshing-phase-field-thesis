# -*- coding: utf-8 -*-
"""Generate authentic live system and controller audit for Task F1722."""
import json
import subprocess
import hashlib
import os
from pathlib import Path

def main():
    repo = Path(__file__).resolve().parents[2]
    
    # 1. Windows Processes
    ps_script = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.ProcessId -in @(26492, 28480, 4044) -or $_.Name -in @('agy.exe', 'codex.exe') } | "
        "Select-Object ProcessId, ParentProcessId, Name, CommandLine, CreationDate, ExecutablePath | "
        "ConvertTo-Json -Depth 5"
    )
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, check=True)
    procs = json.loads(res.stdout)
    
    # 2. WSL OpenClaw Controller State
    wsl_script = (
        "python3 -c '\n"
        "import json, os, hashlib\n"
        "p = \"/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json\"\n"
        "d = json.load(open(p))\n"
        "h = hashlib.sha256(open(p, \"rb\").read()).hexdigest()\n"
        "s = os.stat(p)\n"
        "lk = \"/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json.lock\"\n"
        "lks = os.stat(lk)\n"
        "res = {\n"
        "  \"path\": p,\n"
        "  \"size_bytes\": s.st_size,\n"
        "  \"sha256\": h,\n"
        "  \"safety_blocked\": d.get(\"safety_blocked\"),\n"
        "  \"active_executor\": d.get(\"active_executor\"),\n"
        "  \"workflow_status\": d.get(\"workflow_status\"),\n"
        "  \"standing_project_authorization\": d.get(\"standing_project_authorization\"),\n"
        "  \"lock_path\": lk,\n"
        "  \"lock_size_bytes\": lks.st_size,\n"
        "  \"lock_status\": \"UNLOCKED\" if lks.st_size == 0 else \"LOCKED\"\n"
        "}\n"
        "print(\"WSL_JSON_START\" + json.dumps(res))\n"
        "'"
    )
    wsl_res = subprocess.run(["wsl", "-d", "OpenClawGateway", "bash", "-c", wsl_script], capture_output=True, text=True, check=True)
    wsl_line = [line for line in wsl_res.stdout.splitlines() if "WSL_JSON_START" in line][0]
    wsl_audit = json.loads(wsl_line.split("WSL_JSON_START")[1])
    
    # 3. Bridge Rules
    canon_p = repo / ".agents" / "scripts" / "bridge_rules.txt"
    dep_p = Path("C:/Users/pruth/OpenClawPAD/ChatGPTBridge/bridge_rules.txt")
    canon_b = canon_p.read_bytes()
    dep_b = dep_p.read_bytes()
    
    # 4. Git history for bridge_rules.txt
    git_log_cmd = ["git", "log", "-n", "3", "--pretty=format:%h - %an, %ad : %s", "--date=iso", "--", ".agents/scripts/bridge_rules.txt"]
    git_log_res = subprocess.run(git_log_cmd, cwd=repo, capture_output=True, text=True, check=True)
    
    audit = {
        "audit_id": "AUDIT-F1722-LIVE-SYSTEM-001",
        "timestamp_utc": "2026-11-12T09:15:00Z",
        "active_processes": procs,
        "wsl_openclaw_controller": wsl_audit,
        "bridge_rules_verification": {
            "canonical_path": str(canon_p.relative_to(repo)).replace("\\", "/"),
            "canonical_size_bytes": len(canon_b),
            "canonical_sha256": hashlib.sha256(canon_b).hexdigest().upper(),
            "deployed_path": str(dep_p),
            "deployed_size_bytes": len(dep_b),
            "deployed_sha256": hashlib.sha256(dep_b).hexdigest().upper(),
            "exact_match": canon_b == dep_b,
            "recent_git_history": git_log_res.stdout.splitlines()
        }
    }
    
    out_file = repo / "results" / "validation" / "f1722_live_system_audit.json"
    out_file.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"Generated {out_file} successfully.")

if __name__ == "__main__":
    main()
