"""
Audit the smallest elements in Case 2 PK_F1809_CASE_2_ADAPT_PHYS.inp
to check where the elements clamped by min_element_size_mm = 0.0015 lie,
and determine whether they lie in the outer ligament and how they affect
the 100.00% <= l0/2 coverage claim.
"""
import math

def parse_inp_elements_and_nodes(inp_path):
    nodes = {}
    elements = {}
    with open(inp_path, 'r', encoding='utf-8', errors='ignore') as f:
        section = None
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith('**'):
                continue
            if line_str.startswith('*'):
                header = line_str.upper()
                if header.startswith('*NODE'):
                    section = 'NODE'
                elif header.startswith('*ELEMENT'):
                    section = 'ELEMENT'
                else:
                    section = None
                continue
            
            if section == 'NODE':
                parts = [p.strip() for p in line_str.split(',')]
                if parts and parts[0].isdigit():
                    nid = int(parts[0])
                    x, y = float(parts[1]), float(parts[2])
                    nodes[nid] = (x, y)
            elif section == 'ELEMENT':
                parts = [p.strip() for p in line_str.split(',')]
                if parts and parts[0].isdigit():
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:] if p and p.isdigit()]
                    elements[eid] = nids
    return nodes, elements

def element_centroid_and_area(nids, nodes):
    pts = [nodes[nid] for nid in nids]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    
    # Shoelace formula for polygon area
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    area = 0.5 * abs(area)
    h_char = math.sqrt(area)
    return cx, cy, area, h_char

def main():
    inp_path = 'models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_F1809_CASE_2_ADAPT_PHYS.inp'
    nodes, elements = parse_inp_elements_and_nodes(inp_path)
    print(f"Total elements: {len(elements)}, Total nodes: {len(nodes)}")
    
    l0 = 0.0075
    l0_half = l0 / 2.0  # 0.00375 mm = 3.75 um
    min_size_cfg = 0.0015 # mm = 1.5 um
    
    records = []
    outer_ligament_count = 0
    outer_ligament_le_l0_half = 0
    
    for eid, nids in elements.items():
        cx, cy, area, h = element_centroid_and_area(nids, nodes)
        is_outer_ligament = (0.90 <= cx <= 1.00 and 0.55 <= cy <= 0.75)
        if is_outer_ligament:
            outer_ligament_count += 1
            if h <= l0_half:
                outer_ligament_le_l0_half += 1
        records.append((eid, cx, cy, h, is_outer_ligament))
    
    records.sort(key=lambda r: r[3]) # sort by h
    
    print("\nSmallest 30 elements in the entire mesh:")
    print(f"{'EID':<8} {'cx (mm)':<10} {'cy (mm)':<10} {'h (um)':<10} {'Outer Ligament?':<16} {'Region'}")
    for r in records[:30]:
        eid, cx, cy, h, is_outer = r
        h_um = h * 1000.0
        if cx < 0.55 and abs(cy - 0.5) < 0.02:
            region = "Notch Tip"
        elif 0.55 <= cx <= 0.75 and 0.55 <= cy <= 0.75:
            region = "Hole Boundary"
        elif is_outer:
            region = "Outer Ligament"
        else:
            region = "Other"
        print(f"{eid:<8} {cx:<10.5f} {cy:<10.5f} {h_um:<10.3f} {str(is_outer):<16} {region}")
    
    print(f"\nOuter ligament elements total: {outer_ligament_count}")
    print(f"Outer ligament <= l0/2: {outer_ligament_le_l0_half} ({outer_ligament_le_l0_half / outer_ligament_count * 100:.2f}%)")
    
    outer_records = [r for r in records if r[4]]
    print(f"\nSmallest elements in outer ligament:")
    for r in outer_records[:10]:
        print(f"  EID {r[0]}: cx={r[1]:.5f}, cy={r[2]:.5f}, h={r[3]*1000.0:.3f} um")
    print(f"\nLargest elements in outer ligament:")
    for r in outer_records[-10:]:
        print(f"  EID {r[0]}: cx={r[1]:.5f}, cy={r[2]:.5f}, h={r[3]*1000.0:.3f} um (threshold={l0_half*1000.0:.3f} um)")

if __name__ == '__main__':
    main()
