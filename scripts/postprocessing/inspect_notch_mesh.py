"""
Script to inspect the notch geometry, slit definition, and element sizes around (0,0) in H1 vs PK10R2.
"""

import math

def check_mesh(inp_path):
    nodes = {}
    elements = []
    with open(inp_path) as f:
        in_nodes = False
        in_elem = False
        for line in f:
            line = line.strip()
            if line.startswith('*Node') or line.startswith('*NODE'):
                in_nodes = True
                in_elem = False
                continue
            elif line.startswith('*Element') or line.startswith('*ELEMENT'):
                in_nodes = False
                if 'PHASE_QUAD' in line or 'DISP_QUAD' in line:
                    in_elem = True
                else:
                    in_elem = False
                continue
            elif line.startswith('*'):
                in_nodes = False
                in_elem = False
                continue
            
            if in_nodes and line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except: pass
            elif in_elem and line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    try:
                        elements.append([int(parts[i]) for i in range(1, 5)])
                    except: pass
    
    # Check duplicate nodes along slit y=0, x in [-0.5, 0.0]
    slit_nodes = [n for n, c in nodes.items() if abs(c[1]) < 1e-6 and -0.5 <= c[0] <= 1e-6]
    
    # Check if elements are shared across slit
    top_slit_nodes = set()
    bottom_slit_nodes = set()
    for el in elements:
        coords = [nodes[n] for n in el if n in nodes]
        if len(coords) == 4:
            cy = sum([c[1] for c in coords]) / 4.0
            cx = sum([c[0] for c in coords]) / 4.0
            if cx < -1e-5:
                if cy > 0:
                    for n in el:
                        if abs(nodes[n][1]) < 1e-5 and nodes[n][0] < -1e-5:
                            top_slit_nodes.add(n)
                elif cy < 0:
                    for n in el:
                        if abs(nodes[n][1]) < 1e-5 and nodes[n][0] < -1e-5:
                            bottom_slit_nodes.add(n)
    shared = top_slit_nodes.intersection(bottom_slit_nodes)

    # Find elements around notch tip (0, 0)
    tip_elems = []
    for el in elements:
        coords = [nodes[n] for n in el if n in nodes]
        if len(coords) == 4:
            cx = sum([c[0] for c in coords]) / 4.0
            cy = sum([c[1] for c in coords]) / 4.0
            dist = math.sqrt(cx**2 + cy**2)
            if dist < 0.05:
                # compute min edge length h
                h_min = 1e9
                for i in range(4):
                    p1 = coords[i]
                    p2 = coords[(i+1)%4]
                    edge = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
                    if edge < h_min: h_min = edge
                tip_elems.append((dist, cx, cy, h_min))
    
    tip_elems.sort()
    print("==================================================")
    print("INP: " + inp_path)
    print("Total nodes: " + str(len(nodes)) + ", Total quads: " + str(len(elements)))
    print("Slit shared nodes across y=0: " + str(len(shared)))
    print("Closest elements to notch tip (0,0):")
    for d, cx, cy, h in tip_elems[:8]:
        print("  dist={0:.5f} mm, center=({1:.5f}, {2:.5f}), edge h={3:.5f} mm".format(d, cx, cy, h))


if __name__ == "__main__":
    check_mesh("models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    check_mesh("models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp")
