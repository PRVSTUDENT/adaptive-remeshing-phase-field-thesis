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

in_u1 = in_u3 = False
edges = {} # edge -> count

for line in lines:
    ls = line.strip()
    if ls.startswith("*ELEMENT, TYPE=U1"):
        in_u1 = True; in_u3 = False; continue
    elif ls.startswith("*ELEMENT, TYPE=U3"):
        in_u3 = True; in_u1 = False; continue
    elif ls.startswith("*"):
        in_u1 = in_u3 = False; continue
        
    if (in_u1 or in_u3) and ls:
        p = [int(x.strip()) for x in ls.split(",") if x.strip().isdigit()]
        eid = p[0]
        conn = p[1:]
        # get edges
        for i in range(len(conn)):
            n1 = conn[i]
            n2 = conn[(i+1)%len(conn)]
            edge = tuple(sorted([n1, n2]))
            edges[edge] = edges.get(edge, 0) + 1

# Free boundary edges are those with count == 1
boundary_edges = [e for e, count in edges.items() if count == 1]
boundary_nodes = set()
for n1, n2 in boundary_edges:
    boundary_nodes.add(n1)
    boundary_nodes.add(n2)

print(f"Total boundary edges: {len(boundary_edges)}, boundary nodes: {len(boundary_nodes)}")

# Classify boundary nodes by position
bot_b_nodes = [n for n in boundary_nodes if abs(nodes[n][1] - (-0.5)) < 1e-5]
top_b_nodes = [n for n in boundary_nodes if nodes[n][1] > 0.45] # top boundary
left_b_nodes = [n for n in boundary_nodes if abs(nodes[n][0] - (-0.5)) < 1e-5]
right_b_nodes = [n for n in boundary_nodes if abs(nodes[n][0] - 0.5) < 1e-5]

print(f"Bottom boundary nodes (y=-0.5): {len(bot_b_nodes)}")
print(f"Top boundary nodes (highest y): {len(top_b_nodes)}")
print(f"Left boundary nodes (x=-0.5): {len(left_b_nodes)}")
print(f"Right boundary nodes (x=0.5): {len(right_b_nodes)}")
print(f"Top boundary y values: {sorted(list(set([nodes[n][1] for n in top_b_nodes])))[-5:]}")
