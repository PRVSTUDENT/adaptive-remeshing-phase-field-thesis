import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7'

    remote_code = f"""
with open('{remote_pkg_dir}/M2STATE_FRACFIX_RESTART1R1R7_STEP1.inp') as f:
    lines = f.readlines()

for idx, l in enumerate(lines):
    if '*EQUATION' in l:
        for j in range(0, 15):
            if 0 <= idx + j < len(lines):
                print(str(idx+j+1) + ': ' + lines[idx+j].rstrip())
        break
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
