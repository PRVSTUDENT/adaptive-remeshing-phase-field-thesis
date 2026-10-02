import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
import os

p = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_adaptive_batch/M2ADAPT_MM_FRACFIX_PROD'
if os.path.exists(p):
    print("Listing", p)
    for f in os.listdir(p):
        print(f, os.path.getsize(os.path.join(p, f)))
else:
    print(p, "does not exist")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
