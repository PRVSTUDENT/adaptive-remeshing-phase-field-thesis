import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7'

    remote_code = f"""
with open('{remote_pkg_dir}/M2STATE_FRACFIX_RESTART1R1R7_STEP1.dat') as f:
    lines = f.readlines()

# Parse nodal table
node_data = {{}}
in_table = False
for l in lines:
    if 'THE FOLLOWING TABLE IS PRINTED FOR ALL NODES' in l:
        in_table = True
        continue
    if in_table:
        parts = l.strip().split()
        if len(parts) >= 6 and parts[0].isdigit():
            node = int(parts[0])
            u1 = float(parts[1]) if len(parts) > 1 else 0.0
            u2 = float(parts[2]) if len(parts) > 2 else 0.0
            u3 = float(parts[3]) if len(parts) > 3 else 0.0
            rf1 = float(parts[4]) if len(parts) > 4 else 0.0
            rf2 = float(parts[5]) if len(parts) > 5 else 0.0
            node_data[node] = (u1, u2, u3, rf1, rf2)
        elif 'MAXIMUM' in l:
            in_table = False

print(f"Parsed {{len(node_data)}} nodes")
if 99999 in node_data:
    print("Node 99999:", node_data[99999])

# Read N_BOTTOM from inp
with open('{remote_pkg_dir}/M2STATE_FRACFIX_RESTART1R1R7.inp') as f:
    inp_lines = f.readlines()

bot_nodes = []
in_bot = False
for l in inp_lines:
    if 'NSET=N_BOTTOM' in l:
        in_bot = True
        continue
    if in_bot:
        if l.startswith('*'):
            in_bot = False
            continue
        parts = [int(p.strip()) for p in l.split(',') if p.strip().isdigit()]
        bot_nodes.extend(parts)

sum_bot_rf1 = sum(node_data[n][3] for n in bot_nodes if n in node_data)
sum_bot_rf2 = sum(node_data[n][4] for n in bot_nodes if n in node_data)
print(f"N_BOTTOM (count={{len(bot_nodes)}}) Sum RF1: {{sum_bot_rf1:.6f}}, Sum RF2: {{sum_bot_rf2:.6f}}")

rp_rf1 = node_data[99999][3] if 99999 in node_data else 0.0
print(f"Node 99999 RF1: {{rp_rf1:.6f}}")
print(f"Global Force Balance (RP RF1 + Bot RF1): {{rp_rf1 + sum_bot_rf1:.6f}}")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
