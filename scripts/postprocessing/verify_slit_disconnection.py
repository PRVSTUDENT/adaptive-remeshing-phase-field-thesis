"""
Script to verify whether elements above and below y=0 along the slit x in [-0.5, 0.0]
share common node IDs (unseparated) or use independent node IDs (open physical slit).
"""

import sys

def audit_slit(inp_path):
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
                if 'DISP_QUAD' in line:
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

    # Find elements strictly above slit (y > 0, touching y=0, x < 0)
    top_slit_nodes = set()
    bottom_slit_nodes = set()
    
    for el in elements:
        coords = [nodes[n] for n in el if n in nodes]
        if len(coords) == 4:
            cy = sum([c[1] for c in coords]) / 4.0
            cx = sum([c[0] for c in coords]) / 4.0
            if cx < -1e-5: # left of tip
                if cy > 0: # above slit
                    for n in el:
                        if abs(nodes[n][1]) < 1e-5 and nodes[n][0] < -1e-5:
                            top_slit_nodes.add(n)
                elif cy < 0: # below slit
                    for n in el:
                        if abs(nodes[n][1]) < 1e-5 and nodes[n][0] < -1e-5:
                            bottom_slit_nodes.add(n)

    shared = top_slit_nodes.intersection(bottom_slit_nodes)
    print("==================================================")
    print("SLIT TOPOLOGY AUDIT: " + inp_path)
    print("Top slit nodes count: " + str(len(top_slit_nodes)))
    print("Bottom slit nodes count: " + str(len(bottom_slit_nodes)))
    print("Shared nodes along slit (x < 0, y = 0): " + str(len(shared)))
    if len(shared) == 0:
        print("-> VERDICT: Slit is PHYSICALLY OPEN / FULLY DISCONNECTED (Correct)")
    else:
        print("-> VERDICT: Slit is DEFECTIVELY TIED / CONTINUOUS across " + str(len(shared)) + " nodes!")
        print("   Shared nodes:", list(shared)[:10])

if __name__ == "__main__":
    audit_slit("models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    audit_slit("models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp")
