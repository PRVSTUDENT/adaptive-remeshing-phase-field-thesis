with open("models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/M2STATE_FRACFIX_RESTART2R3.inp", "r") as f:
    lines = f.readlines()

in_u1 = in_u3 = False
active_nodes = set()

for line in lines:
    line_s = line.strip()
    if line_s.startswith("*ELEMENT, TYPE=U1"):
        in_u1 = True
        in_u3 = False
        continue
    elif line_s.startswith("*ELEMENT, TYPE=U3"):
        in_u3 = True
        in_u1 = False
        continue
    elif line_s.startswith("*"):
        in_u1 = in_u3 = False
        continue
        
    if (in_u1 or in_u3) and line_s:
        parts = [p.strip() for p in line_s.split(",")]
        if in_u1 and len(parts) >= 5:
            for n in parts[1:5]:
                if n.isdigit():
                    active_nodes.add(int(n))
        elif in_u3 and len(parts) >= 4:
            for n in parts[1:4]:
                if n.isdigit():
                    active_nodes.add(int(n))

print(f"Total active connected physical nodes in PK10R1: {len(active_nodes)}")
print(f"Min active node ID: {min(active_nodes)}, Max active node ID: {max(active_nodes)}")
