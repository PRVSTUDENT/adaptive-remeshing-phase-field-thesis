import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
with open('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8/M2STATE_FRACFIX_RESTART2R8_STEP1.dat') as f:
    lines = f.readlines()

bottom_rf1 = 0.0
for line in lines:
    p = line.split()
    if len(p) >= 5 and p[0].isdigit():
        nid = int(p[0])
        if 1 <= nid <= 121:
            try:
                if len(p) == 8:
                    bottom_rf1 += float(p[5])
                elif len(p) == 7:
                    bottom_rf1 += float(p[4])
            except:
                pass

print(f"Bottom RF1 Sum (Nodes 1..121): {bottom_rf1:.6f} kN")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
