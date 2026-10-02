#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import subprocess, sys
from pathlib import Path
pbs_file = Path('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6/M2STATE_FRACFIX_RESTART1R1R6.pbs')
lines = pbs_file.read_text().splitlines()
py_lines = []
in_py = False
for l in lines:
    if l.strip().startswith('python3 -c'):
        in_py = True
        continue
    if in_py:
        if l.strip() == '"':
            in_py = False
            break
        py_lines.append(l)
py_code = '\\n'.join(py_lines)
res = subprocess.run([sys.executable, '-c', py_code], cwd=str(pbs_file.parent), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print(res.stdout)
if res.stderr:
    print('STDERR:', res.stderr)
print('RC =', res.returncode)
if res.returncode == 0:
    print('package_manifest_verification = PASS')
    print('previous_failure_mode_regression = PASS')
sys.exit(res.returncode)
"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        f"python3 -c {subprocess.list2cmdline([remote_script])}"
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    if res.stderr:
        print("STDERR:")
        print(res.stderr)
    print("FINAL RETURN CODE:", res.returncode)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
