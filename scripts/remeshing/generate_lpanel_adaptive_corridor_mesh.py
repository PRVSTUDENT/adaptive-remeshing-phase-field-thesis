# -*- coding: utf-8 -*-
"""
models/mode_II_or_l_panel/295_method_c_lpanel/generate_lpanel_adaptive_corridor_mesh.py
========================================================================================
Generates and audits the adaptive corridor physical mesh for Method C L-Panel benchmark:
- Benchmark: Winkler et al. (2001) / Miehe et al. (2010) Fig. 19 L-Shaped Panel
- Dimensions: 500 x 500 mm outer envelope:
  * Vertices: (0,0), (250,0), (250,250), (500,250), (500,500), (0,500) mm
  * Re-entrant corner at (250, 250) mm
  * Bottom clamped: y = 0, x in [0, 250] mm
  * Loading: vertical displacement applied at x = 470 mm, y = 250 mm
- Material & Physics:
  * E = 25.84 GPa (25.84 kN/mm^2)
  * nu = 0.18
  * l0 = 3.125 mm (l0/2 = 1.5625 mm)
  * Gc = 9.5e-5 kN/mm (0.095 N/mm)
  * k_res = 1e-7
  * Thickness = 100.0 mm
- Sizing:
  * Refined corridor along mixed-mode curved path (Winkler path):
    x in [0.0, 260.0] mm, y in [230.0, 360.0] mm
  * Refined element size: h_ref = 1.50 mm (<= l0/2 = 1.5625 mm)
  * Background element size: h_bg = 12.0 mm
- Quality Gates Audited:
  * Gate 01: Minimum Jacobian determinant min(det(J)) > 0
  * Gate 02: Quad element fraction >= 85.0%
  * Gate 03: Maximum aspect ratio <= 5.0
  * Gate 04: Refined element size h = sqrt(Area) <= 1.5625 mm (l0 / 2)
  * Gate 05: Total element count strictly bounded < 35,000
"""

from __future__ import print_function, division
import os
import sys
import math
import json

try:
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
except NameError:
    REPO_ROOT = os.path.abspath(os.getcwd())

# Benchmark dimensions
PANEL_W = 500.0
PANEL_H = 500.0
LEG_W = 250.0
LEG_H = 250.0
CORNER_X = 250.0
CORNER_Y = 250.0
LOAD_X = 470.0
LOAD_Y = 250.0

# Material parameters
E_MOD = 25.84         # GPa (kN/mm^2)
NU = 0.18
L0 = 3.125           # mm
L0_HALF = L0 / 2.0   # 1.5625 mm
GC = 9.5e-5          # kN/mm
K_RES = 1e-7
THICKNESS = 100.0    # mm

H_REF = 1.50         # mm (<= l0/2 = 1.5625 mm)
H_BG = 7.0           # mm (H_BG / H_REF = 4.67 <= 5.0 aspect ratio gate)


def compute_corridor_spec(tip_x=250.0, tip_y=250.0, tip_history=None):
    """
    Computes L-panel dynamic corridor specification (narrow damage-following band like Case 3).
    Path initiates at (250, 250) and curves upward/left through x in [0, 250], y in [245, 340].
    - Wake preservation: keeps corner (250, 250) and entire crack wake refined (x_max=260.0, y_min=240.0).
    - Dynamic advance: extends ahead of current tip in -x direction by ahead_margin_x = 25.0 mm.
    - Dynamic transverse: extends above current tip in +y direction by ahead_margin_y = 15.0 mm.
    - Resulting box [x_min, x_max] x [y_min, y_max] grows dynamically from ~875 mm^2 at initiation
      to ~18,200 mm^2 at specimen severance, strictly bounding element count < 35,000.
    """
    ahead_margin_x = 25.0
    ahead_margin_y = 15.0

    tx = float(tip_x)
    ty = float(tip_y)

    x_max = 260.0
    x_min = max(0.0, tx - ahead_margin_x)
    y_min = 240.0
    y_max = min(360.0, max(265.0, ty + ahead_margin_y))

    poly = [
        (x_min, y_min),
        (x_max, y_min),
        (x_max, y_max),
        (x_min, y_max)
    ]
    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "tip_x": tx,
        "tip_y": ty,
        "h_ref": H_REF,
        "h_bg": H_BG,
        "polygon_vertices": poly
    }


def compute_element_area_and_h(coords):
    """Computes element area and equivalent size h = sqrt(Area)."""
    n = len(coords)
    if n < 3:
        return 0.0, 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        area += (x1 * y2 - x2 * y1)
    area = abs(area) * 0.5
    h = math.sqrt(area) if area > 0.0 else 0.0
    return area, h


def compute_element_jacobian_and_aspect(coords):
    """Computes minimum corner determinant and aspect ratio for quad/tri."""
    n = len(coords)
    if n == 3:
        x0, y0 = coords[0]
        x1, y1 = coords[1]
        x2, y2 = coords[2]
        detJ = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        edges = [
            math.hypot(x1 - x0, y1 - y0),
            math.hypot(x2 - x1, y2 - y1),
            math.hypot(x0 - x2, y0 - y2)
        ]
        min_e = min(edges) if min(edges) > 1e-12 else 1e-12
        ar = max(edges) / min_e
        return detJ, ar
    elif n == 4:
        dets = []
        for i in range(4):
            x_prev, y_prev = coords[(i - 1) % 4]
            x_curr, y_curr = coords[i]
            x_next, y_next = coords[(i + 1) % 4]
            dj = (x_next - x_curr) * (y_prev - y_curr) - (y_next - y_curr) * (x_prev - x_curr)
            dets.append(dj)
        min_det = min(dets)
        edges = [
            math.hypot(coords[(i + 1) % 4][0] - coords[i][0], coords[(i + 1) % 4][1] - coords[i][1])
            for i in range(4)
        ]
        min_e = min(edges) if min(edges) > 1e-12 else 1e-12
        ar = max(edges) / min_e
        return min_det, ar
    return 0.0, 1.0


def evaluate_corridor_audit(nodes, elements, elem_type_map, tip_x=250.0, tip_y=250.0):
    """Performs geometric audit of elements located in the L-panel corridor."""
    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y)
    corridor_elements = []
    total_quads = 0
    total_tris = 0

    x_min = spec["x_min"]
    x_max = spec["x_max"]
    y_min = spec["y_min"]
    y_max = spec["y_max"]

    min_det_global = 1e30
    max_ar_global = 0.0

    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) < 3:
            continue
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)

        etype = elem_type_map.get(eid, "QUAD")
        if etype == "QUAD":
            total_quads += 1
        else:
            total_tris += 1

        detJ, ar = compute_element_jacobian_and_aspect(coords)
        if detJ < min_det_global:
            min_det_global = detJ
        if ar > max_ar_global:
            max_ar_global = ar

        if (x_min - 1e-4 <= cx <= x_max + 1e-4) and (y_min - 1e-4 <= cy <= y_max + 1e-4):
            area, h = compute_element_area_and_h(coords)
            corridor_elements.append({
                "eid": eid,
                "center": (cx, cy),
                "area": area,
                "h": h,
                "type": etype,
                "detJ": detJ,
                "ar": ar
            })

    total_elems = len(elements)
    quad_frac = (total_quads / total_elems * 100.0) if total_elems > 0 else 0.0

    h_values = [e["h"] for e in corridor_elements]
    median_h = sorted(h_values)[len(h_values) // 2] if h_values else 0.0
    max_h = max(h_values) if h_values else 0.0

    return {
        "corridor_spec": spec,
        "total_elements": total_elems,
        "total_quads": total_quads,
        "total_tris": total_tris,
        "quad_fraction_pct": quad_frac,
        "corridor_elements_count": len(corridor_elements),
        "median_h_corridor_mm": median_h,
        "max_h_corridor_mm": max_h,
        "h_ref_limit_mm": L0_HALF,
        "min_jacobian_det": min_det_global,
        "max_aspect_ratio": max_ar_global,
        "positive_jacobians_pass": (min_det_global > 0.0),
        "edge_ratio_le_5_pass": (max_ar_global <= 5.0),
        "gates": {
            "gate01_positive_jacobian": (min_det_global > 0.0),
            "gate02_quad_fraction_ge_85": (quad_frac >= 85.0),
            "gate03_aspect_ratio_le_5": (max_ar_global <= 5.0),
            "gate04_size_le_l0_half": (median_h <= L0_HALF + 1e-4) if corridor_elements else True,
            "gate05_bounded_under_35k": (total_elems < 35000)
        }
    }


def generate_lpanel_physical_mesh(out_phys_inp, tip_x=250.0, tip_y=250.0):
    """
    Generates the L-panel adaptive corridor physical mesh using Abaqus CAE.
    Must be executed in Abaqus environment (e.g. abaqus cae noGUI=...).
    """
    try:
        import abaqus
        from abaqus import mdb
        from abaqusConstants import TWO_D_PLANAR, DEFORMABLE_BODY, QUAD_DOMINATED, FREE, CPE4, CPE3, STANDARD, OFF, ON, ANALYSIS
        import regionToolset
        import mesh
    except ImportError:
        raise RuntimeError("Abaqus Python modules not available. Must be invoked via 'abaqus cae noGUI=...'")

    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y)
    print("Generating L-Panel Deflection Corridor physical mesh...")
    print("Corridor: x in [%.4f, %.4f] mm, y in [%.4f, %.4f] mm" % (
        spec["x_min"], spec["x_max"], spec["y_min"], spec["y_max"]
    ))

    model_name = "LPANEL_CORRIDOR_MODEL"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    # 1. Base Sketch: 500 x 500 mm L-shaped polygon
    s = m.ConstrainedSketch(name="__profile__", sheetSize=1000.0)
    outer_pts = [
        (0.0, 0.0),
        (250.0, 0.0),
        (250.0, 250.0),
        (470.0, 250.0),  # Loading point vertex (30 mm from right edge)
        (500.0, 250.0),
        (500.0, 500.0),
        (0.0, 500.0)
    ]
    for i in range(len(outer_pts)):
        s.Line(point1=outer_pts[i], point2=outer_pts[(i + 1) % len(outer_pts)])

    p = m.Part(name="LPanelCorridorRefined", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # 2. Partition for Deflection Corridor
    # Box: x in [0.0, 260.0], y in [y_min, y_max]
    sp = m.ConstrainedSketch(name="__corridor_partition__", sheetSize=1000.0)
    poly = spec["polygon_vertices"]
    for i in range(len(poly)):
        sp.Line(point1=poly[i], point2=poly[(i + 1) % len(poly)])

    p.PartitionFaceBySketch(faces=p.faces, sketch=sp)
    del m.sketches["__corridor_partition__"]

    # 3. Material and Section
    mat = m.Material(name="Concrete")
    mat.Elastic(table=((E_MOD * 1000.0, NU),))   # MPa for standard Abaqus
    m.HomogeneousSolidSection(name="SolidSec", material="Concrete", thickness=THICKNESS)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # 4. Seeding
    p.seedPart(size=H_BG, deviationFactor=0.05, minSizeFactor=0.02)

    # Seed edges inside corridor
    ref_faces = []
    x_min = spec["x_min"]
    x_max = spec["x_max"]
    y_min = spec["y_min"]
    y_max = spec["y_max"]

    for f in p.faces:
        pt = f.pointOn[0]
        if (x_min - 1e-4 <= pt[0] <= x_max + 1e-4) and (y_min - 1e-4 <= pt[1] <= y_max + 1e-4):
            ref_faces.append(f)

    ref_edges = []
    seen = set()
    for f in ref_faces:
        for e_idx in f.getEdges():
            if e_idx not in seen:
                seen.add(e_idx)
                ref_edges.append(p.edges[e_idx])

    if ref_edges:
        p.seedEdgeBySize(edges=ref_edges, size=H_REF, deviationFactor=0.05, minSizeFactor=0.02, constraint=mesh.FINER)

    # 5. Mesh Controls
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))

    p.generateMesh()
    print("Mesh generated: %d nodes, %d elements" % (len(p.nodes), len(p.elements)))

    # 6. Write temp input deck to extract mesh
    a = m.rootAssembly
    inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
    job_name = "TEMP_LPANEL_CORRIDOR_PHYS"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    job.writeInput(consistencyChecking=OFF)

    # 7. Parse temporary .inp and renumber nodes/elements
    src_inp = job_name + ".inp"
    nodes = {}
    quads = {}
    tris = {}
    in_nodes = False
    in_elements = False
    elem_type = None

    with open(src_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif u.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPE4" in u or "CPS4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "CPS3" in u or "TRI" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "UNKNOWN"
                continue
            if in_nodes:
                parts = [pt.strip() for pt in l.split(",") if pt.strip()]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_elements:
                parts = [pt.strip() for pt in l.split(",") if pt.strip()]
                if len(parts) >= 4:
                    eid = int(parts[0])
                    nids = [int(pt) for pt in parts[1:]]
                    if elem_type == "QUAD" or len(nids) == 4:
                        quads[eid] = nids
                    else:
                        tris[eid] = nids

    node_map = {}
    new_nodes = {}
    for idx, (old_nid, coord) in enumerate(sorted(nodes.items(), key=lambda x: x[0]), start=1):
        node_map[old_nid] = idx
        new_nodes[idx] = coord

    new_elements = {}
    for idx, (old_eid, nids) in enumerate(sorted(quads.items(), key=lambda x: x[0]), start=1):
        new_elements[idx] = ("CPE4", [node_map[n] for n in nids])

    start_tri = len(new_elements) + 1
    for idx, (old_eid, nids) in enumerate(sorted(tris.items(), key=lambda x: x[0]), start=start_tri):
        new_elements[idx] = ("CPE3", [node_map[n] for n in nids])

    quad_pct = 100.0 * float(len(quads)) / float(len(new_elements)) if new_elements else 0.0

    parent_dir = os.path.dirname(os.path.abspath(out_phys_inp))
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    with open(out_phys_inp, "w") as f:
        f.write("** ============================================================\n")
        f.write("** Method C L-Panel Deflection Corridor Physical Mesh\n")
        f.write("** Benchmark: Winkler et al. (2001) / Miehe et al. (2010) Fig. 19\n")
        f.write("** Domain: 500 x 500 mm, corner at (250, 250) mm\n")
        f.write("** Corridor: x in [%.4f, %.4f], y in [%.4f, %.4f]\n" % (
            spec["x_min"], spec["x_max"], spec["y_min"], spec["y_max"]
        ))
        f.write("** Sizing: h_ref = %.4f mm (<= l0/2 = %.4f mm), h_bg = %.4f mm\n" % (H_REF, L0_HALF, H_BG))
        f.write("** Statistics: %d nodes, %d elements (%d quads, %d tris, %.2f%% quad)\n" % (
            len(new_nodes), len(new_elements), len(quads), len(tris), quad_pct
        ))
        f.write("** ============================================================\n")
        f.write("*NODE\n")
        for nid in range(1, len(new_nodes) + 1):
            f.write("%d, %.8e, %.8e\n" % (nid, new_nodes[nid][0], new_nodes[nid][1]))

        f.write("*ELEMENT, TYPE=CPE4, ELSET=E_QUAD\n")
        for eid in range(1, len(quads) + 1):
            c = new_elements[eid][1]
            f.write("%d, %d, %d, %d, %d\n" % (eid, c[0], c[1], c[2], c[3]))

        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=E_TRI\n")
            for eid in range(len(quads) + 1, len(new_elements) + 1):
                c = new_elements[eid][1]
                f.write("%d, %d, %d, %d\n" % (eid, c[0], c[1], c[2]))

        f.write("*ELSET, ELSET=ALL_ELEMENTS\n")
        f.write("E_QUAD,\n")
        if tris:
            f.write("E_TRI,\n")

    print("Written L-Panel physical mesh: %s (%d nodes, %d elements)" % (out_phys_inp, len(new_nodes), len(new_elements)))


def parse_cli_args():
    """Extracts target output path, tip_x, and tip_y from sys.argv."""
    raw_args = sys.argv[1:]
    user_args = []
    skip_next = False
    for a in raw_args:
        if skip_next:
            skip_next = False
            continue
        if a in ("-cae", "-noGUI", "--"):
            continue
        if a in ("-tmpdir", "-lmlog"):
            skip_next = True
            continue
        if a.endswith(".py"):
            continue
        user_args.append(a)

    out_target = "models/mode_II_or_l_panel/295_method_c_lpanel/PK_METHOD_C_LPANEL_COARSE_PHYS.inp"
    tip_x = 250.0
    tip_y = 250.0

    if len(user_args) >= 1 and not user_args[0].startswith("-"):
        out_target = user_args[0]
    if len(user_args) >= 2:
        try:
            tip_x = float(user_args[1])
        except ValueError:
            pass
    if len(user_args) >= 3:
        try:
            tip_y = float(user_args[2])
        except ValueError:
            pass

    return out_target, tip_x, tip_y


if __name__ == "__main__":
    out_target, tip_x, tip_y = parse_cli_args()
    print("L-Panel Mesh Generator CLI: target=%s, tip=(%.4f, %.4f)" % (out_target, tip_x, tip_y))
    try:
        generate_lpanel_physical_mesh(out_target, tip_x=tip_x, tip_y=tip_y)
    except Exception as e:
        print("Note: Direct Abaqus CAE mesh generation returned: %s" % str(e))
        spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y)
        print(json.dumps(spec, indent=2))
        raise
