import os
import sys
import subprocess
from pathlib import Path

SSH_CONFIG = Path(os.environ["USERPROFILE"]) / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/env_test"

def run_remote_sh(local_script_path: str):
    script_name = Path(local_script_path).name
    remote_script = f"{REMOTE_DIR}/{script_name}"

    cmd_scp = [
        "scp", "-F", str(SSH_CONFIG),
        str(local_script_path),
        f"tu_freiberg:{remote_script}"
    ]
    subprocess.run(cmd_scp, check=True)

    cmd_exec = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", f"bash {remote_script}"
    ]
    res = subprocess.run(cmd_exec, capture_output=True, text=True)
    print("=== REMOTE STDOUT ===")
    print(res.stdout)
    if res.stderr:
        print("=== REMOTE STDERR ===")
        print(res.stderr)
    return res.returncode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_remote_helper.py <local_script>")
        sys.exit(1)
    ret = run_remote_sh(sys.argv[1])
    sys.exit(ret)
