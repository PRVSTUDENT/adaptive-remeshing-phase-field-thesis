import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def search_local():
    print("=== Searching Local Repository ===")
    matches = []
    for p in ROOT.rglob("*1386469*"):
        matches.append(str(p))
    for p in ROOT.rglob("*M2ADAPT_MM*"):
        matches.append(str(p))
    for m in sorted(set(matches)):
        print("Local match:", m)

def search_remote():
    print("\n=== Searching Remote Cluster ===")
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
import os
import glob

paths = [
    '/home/pr21vyci/projects/adaptive-remeshing',
    '/scratch/pr21vyci',
    '/home/pr21vyci/adaptive-remeshing',
    '/var/tmp',
]

for base in paths:
    if os.path.exists(base):
        for root, dirs, files in os.walk(base):
            for f in files:
                if '1386469' in f or 'M2ADAPT_MM' in f or '1386470' in f or 'M2ADAPT_PK5' in f:
                    print(os.path.join(root, f))
"""
    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    search_local()
    search_remote()
