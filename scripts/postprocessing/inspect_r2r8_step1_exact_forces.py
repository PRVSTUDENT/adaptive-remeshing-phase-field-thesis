import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
with open('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8/M2STATE_FRACFIX_RESTART2R8_STEP1.dat') as f:
    lines = f.readlines()

in_table = False
rp_rf1 = 0.0
bottom_rf1 = 0.0

for line in lines:
    if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
        in_table = True
        continue
    if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
        in_table = False
        continue
    if in_table:
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit():
            nid = int(parts[0])
            if nid == 99999:
                try:
                    if len(parts) == 8:
                        rp_rf1 = float(parts[5])
                    elif len(parts) == 7:
                        rp_rf1 = float(parts[4])
                except:
                    pass
            if 1 <= nid <= 120:
                try:
                    if len(parts) == 8:
                        rf1 = float(parts[5])
                    elif len(parts) == 7:
                        rf1 = float(parts[4])
                    bottom_rf1 += rf1
                except:
                    pass

print("RP 99999 RF1:", rp_rf1)
print("Bottom RF1 Sum:", bottom_rf1)
print("Global Equilibrium Error:", abs(rp_rf1 + bottom_rf1))
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
