#!/usr/bin/env python3
import subprocess

key_path = r'C:\Users\pruth\.ssh\tu_freiberg_codex'
remote_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R2'

py_code = """
from pathlib import Path
for name in ["submit_m2state_fracfix_restart1r1r2.sh", "M2STATE_FRACFIX_RESTART1R1R2.pbs"]:
    p = Path(name)
    b = p.read_bytes()
    print("NAME:", name)
    print("bytes =", len(b))
    print("CR_count =", b.count(b"\\r"))
    print("LF_count =", b.count(b"\\n"))
    print("CRLF_count =", b.count(b"\\r\\n"))
    lines = b.splitlines(keepends=True)
    if lines:
        print("first_line_raw =", repr(lines[0]))
"""

remote_cmd = f"cd {remote_dir} && file submit_m2state_fracfix_restart1r1r2.sh && file M2STATE_FRACFIX_RESTART1R1R2.pbs && python3 -c '{py_code}'"

cmd = [
    'ssh', '-i', key_path, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no',
    'pr21vyci@mlogin01.hrz.tu-freiberg.de',
    remote_cmd
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
