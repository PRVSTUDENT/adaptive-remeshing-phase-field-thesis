import subprocess
import os
import json
from pathlib import Path

repo = Path(r"D:\Master thesis\Adaptive remeshing")
r6_dir = repo / "models" / "pandey_kumar_mode1" / "108_r6_c3_multi_increment_continuation"
r6_inp = r6_dir / "M1_C3_STAGGERED_R6_CONTINUATION.inp"

# Extract lines up to end of Step 2 (Inc1-Mech1)
lines = r6_inp.read_text(encoding="utf-8").splitlines()
step2_end = None
in_step2 = False
for idx, l in enumerate(lines):
    if "*step" in l.lower() and "inc1-mech1" in l.lower():
        in_step2 = True
    elif in_step2 and "*end step" in l.lower():
        step2_end = idx + 1
        break

diag_lines = lines[:step2_end]
diag_inp = "\n".join(diag_lines) + "\n"

diag_path = r6_dir / "diagnostic_motion.inp"
with open(diag_path, "w", newline="\n", encoding="utf-8") as f:
    f.write(diag_inp)
print(f"Created diagnostic_motion.inp with {len(diag_lines)} lines.")

# Upload diagnostic_motion.inp via scp
ssh_config = os.path.expanduser(r"~/.ssh/codex_config")
remote_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"
scp_exe = r"C:\Program Files\Git\usr\bin\scp.exe"
res_scp = subprocess.run([scp_exe, "-F", ssh_config, str(diag_path), f"tu_freiberg:{remote_dir}/diagnostic_motion.inp"], capture_output=True, text=True)
if res_scp.returncode != 0:
    raise RuntimeError(f"SCP failed: {res_scp.stderr}")
print("Uploaded diagnostic_motion.inp to cluster.")

# Upload extraction script
extract_py = """
from odbAccess import openOdb
import json

odb = openOdb("diagnostic_motion.odb", readOnly=True)
results = {}
for step_name in ["Stage-A", "Inc1-Mech1"]:
    if step_name in odb.steps:
        frame = odb.steps[step_name].frames[-1]
        u = frame.fieldOutputs['U']
        rp_u2 = None
        for val in u.values:
            if val.nodeLabel == 999999:
                rp_u2 = float(val.data[1])
        results[step_name] = {
            "frame_time": float(frame.frameValue),
            "rp_u2": rp_u2
        }
odb.close()

with open("diagnostic_motion_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Diagnostic extraction complete: " + json.dumps(results))
"""

diag_py_path = r6_dir / "extract_diag.py"
with open(diag_py_path, "w", newline="\n", encoding="utf-8") as f:
    f.write(extract_py)

res_scp2 = subprocess.run([scp_exe, "-F", ssh_config, str(diag_py_path), f"tu_freiberg:{remote_dir}/extract_diag.py"], capture_output=True, text=True)
if res_scp2.returncode != 0:
    raise RuntimeError(f"SCP failed: {res_scp2.stderr}")
print("Uploaded extract_diag.py to cluster.")

# Create runner script on remote
run_sh = f"""#!/bin/bash
set -euo pipefail
cd {remote_dir}
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=diagnostic_motion input=diagnostic_motion.inp user=f42_experimental_irreversible_uel.for interactive cpus=1
abaqus python extract_diag.py
cat diagnostic_motion_results.json
"""

diag_sh_path = r6_dir / "run_diagnostic.sh"
with open(diag_sh_path, "w", newline="\n", encoding="utf-8") as f:
    f.write(run_sh)

res_scp3 = subprocess.run([scp_exe, "-F", ssh_config, str(diag_sh_path), f"tu_freiberg:{remote_dir}/run_diagnostic.sh"], capture_output=True, text=True)
if res_scp3.returncode != 0:
    raise RuntimeError(f"SCP failed: {res_scp3.stderr}")
print("Uploaded run_diagnostic.sh to cluster.")

# Execute diagnostic on cluster
exec_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
            "-RemoteCommand", f"chmod +x {remote_dir}/run_diagnostic.sh && {remote_dir}/run_diagnostic.sh",
            "-TimeoutSeconds", "180"]
print("Running diagnostic solve on cluster...")
res_exec = subprocess.run(exec_cmd, capture_output=True, text=True)
print("Execution output:")
print(res_exec.stdout)
if res_exec.stderr:
    print("Stderr:", res_exec.stderr)

# Fetch results
res_fetch = subprocess.run([scp_exe, "-F", ssh_config, f"tu_freiberg:{remote_dir}/diagnostic_motion_results.json", str(r6_dir / "diagnostic_motion_results.json")], capture_output=True, text=True)
if res_fetch.returncode == 0:
    with open(r6_dir / "diagnostic_motion_results.json") as f:
        data = json.load(f)
    print("Fetched diagnostic results successfully:")
    print(json.dumps(data, indent=2))
