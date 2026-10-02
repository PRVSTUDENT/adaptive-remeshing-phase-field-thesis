with open("models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/M2STATE_FRACFIX_RESTART2R3.inp", "r") as f:
    lines = f.readlines()

nodes = {}
in_nodes = False
for line in lines:
    ls = line.strip()
    if ls.startswith("*NODE, NSET=N_PHYSICAL"):
        in_nodes = True
        continue
    elif in_nodes and ls.startswith("*"):
        in_nodes = False
        continue
    if in_nodes and ls:
        p = [x.strip() for x in ls.split(",")]
        if len(p) >= 3 and p[0].isdigit():
            nodes[int(p[0])] = (float(p[1]), float(p[2]))

in_elem = False
elem_nodes = set()
for line in lines:
    ls = line.strip()
    if ls.startswith("*ELEMENT"):
        in_elem = True
        continue
    elif in_elem and ls.startswith("*"):
        in_elem = False
        continue
    if in_elem and ls:
        p = [x.strip() for x in ls.split(",")]
        for x in p[1:]:
            if x.isdigit():
                elem_nodes.add(int(x))

print(f"Total element nodes: {len(elem_nodes)}")
y_vals = [nodes[n][1] for n in elem_nodes if n in nodes]
x_vals = [nodes[n][0] for n in elem_nodes if n in nodes]
print(f"Mesh X range: [{min(x_vals)}, {max(x_vals)}]")
print(f"Mesh Y range: [{min(y_vals)}, {max(y_vals)}]")

# Find nodes at max Y in element nodes
max_y = max(y_vals)
min_y = min(y_vals)
actual_top_nodes = [n for n in elem_nodes if abs(nodes[n][1] - max_y) < 1e-5]
actual_bot_nodes = [n for n in elem_nodes if abs(nodes[n][1] - min_y) < 1e-5]

print(f"Actual top nodes at Y={max_y}: {len(actual_top_nodes)} nodes (IDs: {min(actual_top_nodes)}..{max(actual_top_nodes)})")
print(f"Actual bottom nodes at Y={min_y}: {len(actual_bot_nodes)} nodes (IDs: {min(actual_bot_nodes)}..{max(actual_bot_nodes)})")
