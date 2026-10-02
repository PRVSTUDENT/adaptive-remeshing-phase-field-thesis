import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
import os

candidates = [
    '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_adaptive_batch/M2ADAPT_MM_FRACFIX_PROD/M2ADAPT_MM_FRACFIX_PROD.dat',
    '/scratch/pr21vyci/adaptive-remeshing/runs/M2ADAPT_MM_FRACFIX_PROD_1386469.mmaster02/M2ADAPT_MM_FRACFIX_PROD.dat',
]

for p in candidates:
    if os.path.exists(p):
        print("Found:", p)
        with open(p) as f:
            lines = f.readlines()
        print("Lines:", len(lines))
        # Search for node 99999 or MAXIMUM RF
        for idx, l in enumerate(lines[-200:]):
            print(l.rstrip())
        break
else:
    print("Could not find 1386469 DAT file")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
