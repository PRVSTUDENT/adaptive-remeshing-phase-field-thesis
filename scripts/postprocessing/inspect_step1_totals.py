import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
with open('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8/M2STATE_FRACFIX_RESTART2R8_STEP1.dat') as f:
    lines = f.readlines()

# Find element stress tables or max/min stresses
for i, l in enumerate(lines):
    if "TOTAL FORCE" in l or "REACTION FORCE" in l or "EQUATION" in l:
        print(f"{i+1}: {l.rstrip()}")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
