import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'

    remote_code = """
with open('/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8/M2STATE_FRACFIX_RESTART2R8_STEP1.dat') as f:
    lines = f.readlines()

in_table = False
non_zero_rf = []

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
                    rf1 = float(parts[5])
                    rf2 = float(parts[6])
                elif len(parts) == 7:
                    rf1 = float(parts[4])
                    rf2 = float(parts[5])
                else:
                    rf1 = 0.0
                    rf2 = 0.0
                if abs(rf1) > 1e-6 or abs(rf2) > 1e-6:
                    non_zero_rf.append((nid, rf1, rf2))
            except:
                pass

print(f"Non-zero RF count: {len(non_zero_rf)}")
print("Sample non-zero RF nodes:", non_zero_rf[:15])
if non_zero_rf:
    total_rf1 = sum(r[1] for r in non_zero_rf)
    total_rf2 = sum(r[2] for r in non_zero_rf)
    print(f"Sum RF1 across all non-zero nodes: {total_rf1}")
    print(f"Sum RF2 across all non-zero nodes: {total_rf2}")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
