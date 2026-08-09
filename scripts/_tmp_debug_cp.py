#!/usr/bin/env python3
import json
from pathlib import Path

p = Path("models/generated/mode_ii/reference_convergence/M2REF_H0/M2REF_H0.inp")
text = p.read_text(encoding="utf-8")

nodes = {}
u1_elems = {}
in_n = in_e = False

for line in text.splitlines():
    s = line.strip()
    if not s or s.startswith("**"):
        continue
    sl = s.lower()
    if sl.startswith("*node"):
        in_n = True
        in_e = False
        continue
    elif sl.startswith("*element, type=u1"):
        in_e = True
        in_n = False
        continue
    elif s.startswith("*"):
        in_n = in_e = False

    if in_n and "," in s:
        parts = [x.strip() for x in s.split(",")]
        if len(parts) >= 3 and parts[0].isdigit():
            nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
    elif in_e and "," in s:
        parts = [x.strip() for x in s.split(",")]
        if len(parts) >= 5 and parts[0].isdigit():
            u1_elems[int(parts[0])] = [int(x) for x in parts[1:5]]

print(f"Total nodes: {len(nodes)}, Total elements: {len(u1_elems)}")

for eid, conn in u1_elems.items():
    coords = [nodes[n] for n in conn if n in nodes]
    if len(coords) == 4:
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = coords
        # Shoelace signed area
        signed_area = 0.5 * ((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
        # Cross products of edges: 1->2, 2->3, 3->4, 4->1
        cp1 = (x2 - x1)*(y3 - y2) - (y2 - y1)*(x3 - x2)
        cp2 = (x3 - x2)*(y4 - y3) - (y3 - y2)*(x4 - x3)
        cp3 = (x4 - x3)*(y1 - y4) - (y4 - y3)*(x1 - x4)
        cp4 = (x1 - x4)*(y2 - y1) - (y1 - y4)*(x2 - x1)
        
        tol = -1.0e-12
        is_convex = (cp1 >= tol and cp2 >= tol and cp3 >= tol and cp4 >= tol) or (cp1 <= -tol and cp2 <= -tol and cp3 <= -tol and cp4 <= -tol)
        
        if not is_convex or abs(signed_area) <= 1.0e-12:
            print(f"Elem {eid}: area={signed_area:.6e}, cp1={cp1:.6e}, cp2={cp2:.6e}, cp3={cp3:.6e}, cp4={cp4:.6e}")
