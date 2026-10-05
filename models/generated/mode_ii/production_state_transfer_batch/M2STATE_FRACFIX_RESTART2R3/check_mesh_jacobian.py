# Check Jacobian and inversion for PK10R1 mesh elements
with open("M2STATE_FRACFIX_RESTART2R3.inp", "r") as f:
    lines = f.readlines()

nodes = {}
in_nodes = False
in_u1 = False
u1_elems = {}

for line in lines:
    line = line.strip()
    if line.startswith("*NODE"):
        in_nodes = True
        in_u1 = False
        continue
    elif line.startswith("*ELEMENT, TYPE=U1"):
        in_nodes = False
        in_u1 = True
        continue
    elif line.startswith("*"):
        in_nodes = False
        in_u1 = False
        continue
    
    if in_nodes and line:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            nid = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            nodes[nid] = (x, y)
    elif in_u1 and line:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5:
            eid = int(parts[0])
            n1, n2, n3, n4 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
            u1_elems[eid] = (n1, n2, n3, n4)

print(f"Loaded {len(nodes)} nodes, {len(u1_elems)} U1 elements")

# Check simplified DETJ vs true DETJ at 4 Gauss points
neg_simple_detj = 0
neg_true_detj = 0

xg4 = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
yg4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]

for eid, (n1, n2, n3, n4) in u1_elems.items():
    x1, y1 = nodes[n1]
    x2, y2 = nodes[n2]
    x3, y3 = nodes[n3]
    x4, y4 = nodes[n4]
    
    # Simplified DETJ from Fortran
    simple_detj = ((x2 - x1)*(y4 - y1) - (x4 - x1)*(y2 - y1)) / 4.0
    if simple_detj <= 0:
        neg_simple_detj += 1
        if neg_simple_detj <= 5:
            print(f"Negative/Zero simple DETJ at elem {eid}: {simple_detj}, nodes: ({n1},{n2},{n3},{n4})")
            print(f"  Coords: ({x1},{y1}), ({x2},{y2}), ({x3},{y3}), ({x4},{y4})")

print(f"Total elements with simple_detj <= 0: {neg_simple_detj} / {len(u1_elems)}")
