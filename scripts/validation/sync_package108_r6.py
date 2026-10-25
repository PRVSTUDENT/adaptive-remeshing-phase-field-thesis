import subprocess
import os
import hashlib
from pathlib import Path

repo = Path(r"D:\Master thesis\Adaptive remeshing")
r6_dir = repo / "models" / "pandey_kumar_mode1" / "108_r6_c3_multi_increment_continuation"
ssh_config = os.path.expanduser(r"~/.ssh/codex_config")
remote_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"

# 1. Create remote dir
cmd_mkdir = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
             "-RemoteCommand", f"mkdir -p {remote_dir}"]
subprocess.run(cmd_mkdir, check=True)

# 2. Upload files via scp
files_to_upload = [
    "M1_C3_STAGGERED_R6_CONTINUATION.inp",
    "d_lower_bounds.csv",
    "f42_experimental_irreversible_uel.for",
    "submit_M1_C3_STAGGERED_R6.pbs",
    "job_notifications.sh",
    "run_pkg108_r6_datacheck.sh",
    "M1_C3_STAGGERED_R6_AUTHORIZATION.json"
]

scp_exe = r"C:\Program Files\Git\usr\bin\scp.exe"
for f in files_to_upload:
    local_path = str(r6_dir / f)
    target = f"tu_freiberg:{remote_dir}/{f}"
    print(f"Uploading {f} via scp...")
    res = subprocess.run([scp_exe, "-F", ssh_config, local_path, target], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error uploading {f}: {res.stderr}")
        raise RuntimeError(f"SCP failed: {res.stderr}")
    print(f"Uploaded {f} successfully.")

# Set executable bits on scripts
cmd_chmod = ["powershell", "-NoProfile", "-ExecutionPolicy Bypass",
             "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
             "-RemoteCommand", f"chmod +x {remote_dir}/*.sh {remote_dir}/*.pbs"]
# wait, pass ExecutionPolicy and Bypass as separate args
cmd_chmod = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
             "-RemoteCommand", f"chmod +x {remote_dir}/run_pkg108_r6_datacheck.sh {remote_dir}/submit_M1_C3_STAGGERED_R6.pbs"]
subprocess.run(cmd_chmod, check=True)

# Verify hashes on remote
verify_cmd = f"cd {remote_dir} && sha256sum " + " ".join(files_to_upload)
cmd_verify = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
              "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
              "-RemoteCommand", verify_cmd]
res_v = subprocess.run(cmd_verify, capture_output=True, text=True)
print("Remote verification output:")
print(res_v.stdout)
if res_v.stderr:
    print(res_v.stderr)
