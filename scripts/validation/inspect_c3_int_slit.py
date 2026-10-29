import re

nodes = {}
elements = {}
reading = None

with open("models/pandey_kumar_mode1/141_c3_int_donor_monotonic/M1_C3_INT_DONOR_MONOTONIC.inp", "r") as f:
    for line in f:
        l = line.strip()
        if not l or l.startswith("**"):
            continue
        u = l.upper()
        if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
            reading = "NODE"
            continue
        elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
            reading = "ELEM"
            continue
        elif u.startswith("*"):
            reading = None
            continue

        if reading == "NODE":
            p = [x.strip() for x in l.split(",")]
            if len(p) >= 3:
                nid = int(p[0])
                if nid <= 2610:
                    nodes[nid] = (float(p[1]), float(p[2]))
        elif reading == "ELEM":
            p = [int(x.strip()) for x in l.split(",") if x.strip().isdigit()]
            if len(p) == 5:
                elements[p[0]] = p[1:5]

print("Total physical nodes:", len(nodes))
print("Total physical quads:", len(elements))

slit_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.050) < 1.0e-5 and x <= 0.040 + 1.0e-5]
print("Slit nodes along y=0.05, x<=0.04:", len(slit_nodes))

# Find node pairs by x-coordinate
from collections import defaultdict
by_x = defaultdict(list)
for nid in slit_nodes:
    x, y = nodes[nid]
    by_x[round(x, 7)].append(nid)

print("Unique x-coordinates along slit:", len(by_x))
for x_val in sorted(by_x.keys()):
    nids = by_x[x_val]
    # Check elements sharing these nodes
    info = []
    for n in nids:
        attached_elems = [eid for eid, conn in elements.items() if n in conn]
        centers_y = [sum(nodes[m][1] for m in elements[eid])/4.0 for eid in attached_elems]
        side = "UPPER" if all(cy > 0.05 for cy in centers_y) else ("LOWER" if all(cy < 0.05 for cy in centers_y) else "SHARED")
        info.append((n, side, len(attached_elems)))
    print("  x=%.7f: %s" % (x_val, info))
