import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
with open('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8/M2STATE_FRACFIX_RESTART2R8_STEP1.dat') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
        for j in range(-5, 25):
            if 0 <= i + j < len(lines):
                print(f"{i+j+1}: {lines[i+j].rstrip()}")
        break
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
