import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
with open('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8/M2STATE_FRACFIX_RESTART2R8_STEP1.dat') as f:
    lines = f.readlines()

in_table = False
non_zero_u = []

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
            try:
                if len(parts) == 8:
                    u1 = float(parts[2])
                    u2 = float(parts[3])
                    u3 = float(parts[4])
                elif len(parts) == 7:
                    u1 = float(parts[1])
                    u2 = float(parts[2])
                    u3 = float(parts[3])
                if abs(u1) > 1e-6 or abs(u2) > 1e-6 or abs(u3) > 1e-6:
                    non_zero_u.append((nid, u1, u2, u3))
            except:
                pass

print(f"Non-zero U count: {len(non_zero_u)}")
print("Sample non-zero U nodes:", non_zero_u[:15])
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
