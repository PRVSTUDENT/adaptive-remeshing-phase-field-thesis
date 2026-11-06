# -*- coding: utf-8 -*-
"""Upload extraction runner script to cluster scratch directory."""
import base64
import subprocess
from pathlib import Path

local_script = Path("scripts/postprocessing/correlate_pilot_damage_mesh.py")
content = local_script.read_bytes()
data64 = base64.b64encode(content).decode("ascii")

remote_dir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_pilot"
remote_target = f"{remote_dir}/correlate_pilot_damage_mesh.py"

install_code = "import base64,pathlib,sys,os; p=pathlib.Path(sys.argv[1]); p.write_bytes(base64.b64decode(sys.argv[2])); os.chmod(sys.argv[1], 0o755); print('Runner uploaded successfully')"
code64 = base64.b64encode(install_code.encode("utf-8")).decode("ascii")

remote_cmd = f"python3 -c 'import base64,sys;exec(base64.b64decode(sys.argv.pop(1)))' {code64} {remote_target} {data64}"

ps_cmd = [
    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", r".\.agents\scripts\Invoke-GuardedSsh.ps1",
    "-RemoteCommand", remote_cmd
]

res = subprocess.run(ps_cmd, capture_output=True, text=True)
print("Exit code:", res.returncode)
print("STDOUT:", res.stdout.strip())
print("STDERR:", res.stderr.strip())
