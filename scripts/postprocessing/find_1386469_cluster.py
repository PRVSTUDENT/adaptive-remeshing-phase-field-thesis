import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
import os

for root, dirs, files in os.walk('/home/pr21vyci/projects/adaptive-remeshing'):
    for f in files:
        if '1386469' in f or 'M2ADAPT_MM' in f:
            print(os.path.join(root, f))
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
