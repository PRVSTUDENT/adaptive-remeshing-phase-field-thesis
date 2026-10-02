import os
import sys
import hashlib
import math
import json

INP_PATH = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"
EXPECTED_INP_SHA256 = "667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be"

def verify_sha256(path, expected):
    with open(path, "rb") as f:
        data = f.read()
    actual = hashlib.sha256(data).hexdigest().lower()
    print("INP SHA256 Actual:   %s" % actual)
    print("INP SHA256 Expected: %s" % expected)
    assert actual == expected, "INP SHA256 mismatch!"
    return actual

def parse_pk10r2_inp(path):
    nodes = {}
    u1_elements = {}
    u2_elements = {}
    vis_elements = {}
    node_sets = {}
    element_sets = {}
    equations = []

    current_section = None
    current_set_name = None
    current_elem_type = None

    with open(path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue

            if l.startswith("*"):
                parts = [p.strip() for p in l.split(",")]
                keyword = parts[0].upper()

                if keyword == "*NODE":
                    current_section = "NODE"
                    continue
                elif keyword == "*ELEMENT":
                    current_section = "ELEMENT"
                    current_elem_type = None
                    for p in parts[1:]:
                        if "TYPE=" in p.upper():
                            current_elem_type = p.upper().split("=")[1].strip()
                    continue
                elif keyword == "*NSET":
                    current_section = "NSET"
                    current_set_name = None
                    for p in parts[1:]:
                        if "NSET=" in p.upper():
                            current_set_name = p.split("=")[1].strip()
                    if current_set_name and current_set_name not in node_sets:
                        node_sets[current_set_name] = []
                    continue
                elif keyword == "*ELSET":
                    current_section = "ELSET"
                    current_set_name = None
                    for p in parts[1:]:
                        if "ELSET=" in p.upper():
                            current_set_name = p.split("=")[1].strip()
                    if current_set_name and current_set_name not in element_sets:
                        element_sets[current_set_name] = []
                    continue
                elif keyword == "*EQUATION":
                    current_section = "EQUATION"
                    continue
                else:
                    current_section = "OTHER"
                    continue

            if current_section == "NODE":
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif current_section == "ELEMENT":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        conn = tuple(int(p) for p in parts[1:5])
                        if current_elem_type == "U1":
                            u1_elements[eid] = conn
                        elif current_elem_type == "U2":
                            u2_elements[eid] = conn
                        elif current_elem_type in ("CPE4", "CPE4R"):
                            vis_elements[eid] = conn
                    except ValueError:
                        pass
            elif current_section == "NSET" and current_set_name:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                for p in parts:
                    try:
                        node_sets[current_set_name].append(int(p))
                    except ValueError:
                        pass
            elif current_section == "ELSET" and current_set_name:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                for p in parts:
                    try:
                        element_sets[current_set_name].append(int(p))
                    except ValueError:
                        pass
            elif current_section == "EQUATION":
                equations.append(l)

    return nodes, u1_elements, u2_elements, vis_elements, node_sets, element_sets, equations

def quad_metrics(coords):
    # coords: [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    # Edge lengths
    edges = []
    for i in range(4):
        p1 = coords[i]
        p2 = coords[(i+1)%4]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        edges.append(math.sqrt(dx*dx + dy*dy))

    min_edge = min(edges)
    max_edge = max(edges)

    # Shoelace formula for area
    area = 0.5 * abs(
        (coords[0][0]*coords[1][1] - coords[1][0]*coords[0][1]) +
        (coords[1][0]*coords[2][1] - coords[2][0]*coords[1][1]) +
        (coords[2][0]*coords[3][1] - coords[3][0]*coords[2][1]) +
        (coords[3][0]*coords[0][1] - coords[0][0]*coords[3][1])
    )

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    hx = max(xs) - min(xs)
    hy = max(ys) - min(ys)

    aspect_ratio = max(edges) / min(edges) if min_edge > 0 else 1.0

    # Jacobian determinants at 2x2 Gauss points
    xg = (-0.577350269189626, 0.577350269189626)
    yg = (-0.577350269189626, 0.577350269189626)
    jac_positive = True
    min_det_j = 1e9

    for xi in xg:
        for eta in yg:
            dn_dxi = (
                -0.25 * (1.0 - eta),
                 0.25 * (1.0 - eta),
                 0.25 * (1.0 + eta),
                -0.25 * (1.0 + eta)
            )
            dn_deta = (
                -0.25 * (1.0 - xi),
                -0.25 * (1.0 + xi),
                 0.25 * (1.0 + xi),
                 0.25 * (1.0 - xi)
            )
            j11 = sum(dn_dxi[i] * coords[i][0] for i in range(4))
            j12 = sum(dn_deta[i] * coords[i][0] for i in range(4))
            j21 = sum(dn_dxi[i] * coords[i][1] for i in range(4))
            j22 = sum(dn_deta[i] * coords[i][1] for i in range(4))
            det_j = j11 * j22 - j12 * j21
            if det_j <= 0.0:
                jac_positive = False
            if det_j < min_det_j:
                min_det_j = det_j

    return {
        "min_edge": min_edge,
        "max_edge": max_edge,
        "area": area,
        "hx": hx,
        "hy": hy,
        "aspect_ratio": aspect_ratio,
        "jac_positive": jac_positive,
        "min_det_j": min_det_j,
        "center": (sum(xs)/4.0, sum(ys)/4.0)
    }

def main():
    print("================================================================================")
    print("STRICT OFFLINE PK10R2 FROZEN MESH AUDIT")
    print("================================================================================")

    verify_sha256(INP_PATH, EXPECTED_INP_SHA256)

    nodes, u1_elems, u2_elems, vis_elems, nsets, elsets, equations = parse_pk10r2_inp(INP_PATH)

    rp_node_id = 100000
    is_rp_in_nodes = (rp_node_id in nodes)
    physical_nodes = {nid: c for nid, c in nodes.items() if nid != rp_node_id}

    print("\n--- 1. Node & Element Counts ---")
    print("Total Nodes in *NODE:     %d" % len(nodes))
    print("Physical Nodes:           %d" % len(physical_nodes))
    print("Auxiliary RP Node Count:  %d (Node ID: %s)" % (1 if is_rp_in_nodes else 0, str(rp_node_id if is_rp_in_nodes else None)))
    print("Physical Quads (Layer 1): %d" % len(u1_elems))
    print("Layer 2 Elements (U2):    %d" % len(u2_elems))
    print("Layer 3 Elements (CPE4):  %d" % len(vis_elems))
    print("Total Layered Elements:   %d" % (len(u1_elems) + len(u2_elems) + len(vis_elems)))

    all_x = [c[0] for c in physical_nodes.values()]
    all_y = [c[1] for c in physical_nodes.values()]
    print("\n--- Domain Bounds ---")
    print("X min: %.6f, X max: %.6f (Domain width:  %.6f)" % (min(all_x), max(all_x), max(all_x) - min(all_x)))
    print("Y min: %.6f, Y max: %.6f (Domain height: %.6f)" % (min(all_y), max(all_y), max(all_y) - min(all_y)))

    # 2. Geometric Metrics
    print("\n--- 2. Element Dimensions & Quality Metrics ---")
    elem_metrics = {}
    pos_jac_count = 0
    neg_jac_count = 0

    for eid, conn in u1_elems.items():
        coords = [nodes[nid] for nid in conn]
        m = quad_metrics(coords)
        elem_metrics[eid] = m
        if m["jac_positive"]:
            pos_jac_count += 1
        else:
            neg_jac_count += 1

    min_edges = [m["min_edge"] for m in elem_metrics.values()]
    max_edges = [m["max_edge"] for m in elem_metrics.values()]
    areas = [m["area"] for m in elem_metrics.values()]
    aspect_ratios = sorted([m["aspect_ratio"] for m in elem_metrics.values()])
    hxs = [m["hx"] for m in elem_metrics.values()]
    hys = [m["hy"] for m in elem_metrics.values()]

    print("Positive Jacobian Elements: %d / %d" % (pos_jac_count, len(u1_elems)))
    print("Zero / Negative Jacobian:   %d" % neg_jac_count)
    print("Total Physical Mesh Area:   %.8f mm^2" % sum(areas))
    print("Minimum Edge Length:        %.8f mm" % min(min_edges))
    print("Maximum Edge Length:        %.8f mm" % max(max_edges))
    print("Minimum Element Area:       %.10f mm^2" % min(areas))
    print("Maximum Element Area:       %.10f mm^2" % max(areas))
    print("Aspect Ratio Min:           %.6f" % aspect_ratios[0])
    print("Aspect Ratio Median:        %.6f" % aspect_ratios[len(aspect_ratios)//2])
    print("Aspect Ratio Max:           %.6f" % aspect_ratios[-1])

    # 3. Adjacency and Neighbor Sizing Ratio
    print("\n--- 3. Mesh Grading and Neighbor Sizing Metrics ---")
    # Build edge to element map
    edge_to_elems = {}
    for eid, conn in u1_elems.items():
        for i in range(4):
            n1 = min(conn[i], conn[(i+1)%4])
            n2 = max(conn[i], conn[(i+1)%4])
            edge = (n1, n2)
            if edge not in edge_to_elems:
                edge_to_elems[edge] = []
            edge_to_elems[edge].append(eid)

    # Element adjacency
    elem_neighbors = {eid: set() for eid in u1_elems}
    for edge, shared_eids in edge_to_elems.items():
        if len(shared_eids) == 2:
            e1, e2 = shared_eids
            elem_neighbors[e1].add(e2)
            elem_neighbors[e2].add(e1)

    max_adj_ratio = 1.0
    for eid, nbrs in elem_neighbors.items():
        h_e = math.sqrt(elem_metrics[eid]["area"])
        for nbr_id in nbrs:
            h_nbr = math.sqrt(elem_metrics[nbr_id]["area"])
            ratio = max(h_e, h_nbr) / min(h_e, h_nbr)
            if ratio > max_adj_ratio:
                max_adj_ratio = ratio

    global_ratio = max(max_edges) / min(min_edges)
    print("Global h_max / h_min:                           %.6f" % global_ratio)
    print("Maximum Adjacent-Element Size Ratio (Neighbor): %.6f" % max_adj_ratio)
    print("Maximum Element Aspect Ratio:                   %.6f" % aspect_ratios[-1])

    # 4. Notch / Slit Topology Audit
    print("\n--- 4. Notch / Slit Topology Audit ---")
    # Find all nodes with y == 0 and x <= 0
    slit_nodes = {}
    for nid, (x, y) in physical_nodes.items():
        if abs(y) < 1e-7 and x <= 1e-7:
            # Group by rounded x coordinate
            rx = round(x, 6)
            if rx not in slit_nodes:
                slit_nodes[rx] = []
            slit_nodes[rx].append(nid)

    print("Total X-stations along notch (x in [-0.5, 0.0], y = 0): %d" % len(slit_nodes))
    split_stations = 0
    duplicate_node_count = 0
    tip_nodes = []

    for rx in sorted(slit_nodes.keys()):
        nids = slit_nodes[rx]
        if len(nids) == 2:
            split_stations += 1
            duplicate_node_count += 2
        elif len(nids) == 1:
            if abs(rx) < 1e-7:
                tip_nodes = nids

    print("Slit Split Station Count (x < 0):   %d" % split_stations)
    print("Total Duplicate Slit Nodes (pairs): %d nodes (%d pairs)" % (duplicate_node_count, split_stations))
    print("Crack Tip Node at x = 0:            Node %s (Count: %d)" % (str(tip_nodes), len(tip_nodes)))

    # Verify elements above vs below slit
    upper_slit_elems = []
    lower_slit_elems = []
    for eid, conn in u1_elems.items():
        c_y = elem_metrics[eid]["center"][1]
        c_x = elem_metrics[eid]["center"][0]
        if c_x < 0.0:
            if 0.0 < c_y < 0.05:
                upper_slit_elems.append(eid)
            elif -0.05 < c_y < 0.0:
                lower_slit_elems.append(eid)

    # Check if any element connects across slit for x < 0
    cross_connected = False
    for eid, conn in u1_elems.items():
        c_x = elem_metrics[eid]["center"][0]
        if c_x < -1e-6:
            has_pos_y = any(nodes[nid][1] > 1e-6 for nid in conn)
            has_neg_y = any(nodes[nid][1] < -1e-6 for nid in conn)
            if has_pos_y and has_neg_y:
                cross_connected = True
                print("WARNING: Element %d spans across slit!" % eid)

    print("Slit Elements Cross-Connected across y=0 (x<0): %s" % ("YES (Defective)" if cross_connected else "NO (Proper Physical Slit)"))

    # Check intact ligament connectivity for x > 0
    ligament_nodes = {}
    for nid, (x, y) in physical_nodes.items():
        if abs(y) < 1e-7 and x > 1e-7:
            rx = round(x, 6)
            if rx not in ligament_nodes:
                ligament_nodes[rx] = []
            ligament_nodes[rx].append(nid)

    all_ligament_single = all(len(nids) == 1 for nids in ligament_nodes.values())
    print("Intact Ligament (x > 0) Single-Node Continuous: %s (%d stations checked)" % (
        "YES (Fully Connected)" if all_ligament_single else "NO", len(ligament_nodes)
    ))

    # 5. Process-Zone Resolution Sequence
    print("\n--- 5. Process-Zone Resolution Sequence ---")
    pz_elems = [m for m in elem_metrics.values() if abs(m["center"][0]) < 0.05 and abs(m["center"][1]) < 0.05]
    pz_min_edge = min(m["min_edge"] for m in pz_elems)
    pz_max_edge = max(m["max_edge"] for m in pz_elems)
    print("Refined Corridor Bounds: x in [-0.05, 0.05], y in [-0.05, 0.05]")
    print("Element Count in Corridor: %d" % len(pz_elems))
    print("Corridor Edge Sizing: Min = %.6f mm, Max = %.6f mm" % (pz_min_edge, pz_max_edge))

    # Elements at notch tip
    tip_elems = [m for m in elem_metrics.values() if abs(m["center"][0]) < 0.005 and abs(m["center"][1]) < 0.005]
    print("Tip Element Size (h_local): %.6f mm (hx = %.6f, hy = %.6f)" % (
        tip_elems[0]["min_edge"], tip_elems[0]["hx"], tip_elems[0]["hy"]
    ))

    # Far field elements (corners)
    ff_elems = [m for m in elem_metrics.values() if abs(m["center"][0]) > 0.45 and abs(m["center"][1]) > 0.45]
    print("Far-Field Element Size (h_global): %.6f mm (hx = %.6f, hy = %.6f)" % (
        ff_elems[0]["max_edge"], ff_elems[0]["hx"], ff_elems[0]["hy"]
    ))

if __name__ == "__main__":
    main()
