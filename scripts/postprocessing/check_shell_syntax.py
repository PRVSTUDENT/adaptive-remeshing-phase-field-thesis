#!/usr/bin/env python3
"""Run bash syntaxcheck and verify CR_count = 0 on cluster."""
import os
import subprocess
import sys

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_cmd = (
        "cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6 && "
        "bash -n submit_m2state_fracfix_restart1r1r6.sh && "
        "bash -n M2STATE_FRACFIX_RESTART1R1R6.pbs && "
        "echo BASH_SYNTAX_OK && "
        "python3 -c \"from pathlib import Path\nfor f in ['submit_m2state_fracfix_restart1r1r6.sh', 'M2STATE_FRACFIX_RESTART1R1R6.pbs']:\n cr = Path(f).read_bytes().count(b'\\r')\n print(f'{f}: CR_count = {cr}')\n assert cr == 0\""
    )
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        remote_cmd
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    return res.returncode

if __name__ == "__main__":
    sys.exit(main())
