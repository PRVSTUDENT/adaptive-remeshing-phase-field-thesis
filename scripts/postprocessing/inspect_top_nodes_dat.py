import os
import subprocess

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7'

    remote_code = f"""
with open('{remote_pkg_dir}/M2STATE_FRACFIX_RESTART1R1R7_STEP1.dat') as f:
    lines = f.readlines()

# Read N_TOP from inp
with open('{remote_pkg_dir}/M2STATE_FRACFIX_RESTART1R1R7.inp') as f:
    inp_lines = f.readlines()

top_nodes = []
in_top = False
for l in inp_lines:
    if 'NSET=N_TOP' in l:
        in_top = True
        continue
    if in_top:
        if l.startswith('*'):
            in_top = False
            continue
        parts = [int(p.strip()) for p in l.split(',') if p.strip().isdigit()]
        top_nodes.extend(parts)

print("Total top nodes in N_TOP:", len(top_nodes))

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

print("Sample top nodes:")
sum_top_rf1 = 0.0
for n in top_nodes[:10]:
    print(f"Node {{n}}: U1={{node_data[n][0]:.6e}}, U2={{node_data[n][1]:.6e}}, RF1={{node_data[n][3]:.6e}}, RF2={{node_data[n][4]:.6e}}")

for n in top_nodes:
    if n in node_data:
        sum_top_rf1 += node_data[n][3]

print(f"Sum RF1 on all {{len(top_nodes)}} top nodes: {{sum_top_rf1:.6f}}")
print(f"Node 99999: U1={{node_data[99999][0]:.6e}}, RF1={{node_data[99999][3]:.6e}}")
"""

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'python3']
    res = subprocess.run(cmd, input=remote_code, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
