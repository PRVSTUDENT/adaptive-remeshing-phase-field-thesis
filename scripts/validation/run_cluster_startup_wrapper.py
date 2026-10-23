import os
import subprocess
from pathlib import Path

SSH_CONFIG = Path(os.environ["USERPROFILE"]) / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/env_test"

for fname in ["test_cluster_pdas_startup.py", "run_cluster_pdas_startup.sh"]:
    local_path = Path("scripts/validation") / fname
    cmd = ["scp", "-F", str(SSH_CONFIG), str(local_path), f"tu_freiberg:{REMOTE_DIR}/{fname}"]
    subprocess.run(cmd, check=True)

cmd_exec = [
    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
    r".\.agents\scripts\Invoke-GuardedSsh.ps1",
    "-RemoteCommand", f"bash {REMOTE_DIR}/run_cluster_pdas_startup.sh"
]
res = subprocess.run(cmd_exec, capture_output=True, text=True)
print("=== REMOTE OUTPUT ===")
print(res.stdout)
if res.stderr:
    print("=== REMOTE STDERR ===")
    print(res.stderr)
print("Exit code:", res.returncode)
