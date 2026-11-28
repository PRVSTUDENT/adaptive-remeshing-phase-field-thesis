# -*- coding: utf-8 -*-
"""
models/complex_mixed_load/generate_mixed_load_mesh.py
=====================================================
Task: METHOD-C-COMPLEX-MODELS (Problem 3)
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-004 / HND-METHOD-C-COMPLEX-005

Generates and audits the narrow damage-following band physical mesh for
Problem 3: Notch + Hole under Combined Tension + Shear (ux = 0.5 * uy):
- Geometry:
  * 1.0 x 1.0 mm square plate: [0.0, 1.0] x [0.0, 1.0] mm
  * 0.5 mm edge notch inclined at +45 degrees from (0.0, 0.5) to (0.353553, 0.853553) mm
  * Circular hole at center (0.65, 0.65) mm, radius R = 0.10 mm
- Physics & Material:
  * E = 210.0 GPa (210.0 kN/mm^2)
  * nu = 0.30
  * l0 = 0.0075 mm (l0 / 2 = 0.00375 mm)
  * Gc = 0.0027 kN/mm (2.7 N/mm)
  * k_res = 1.0e-7
  * Thickness = 1.0 mm
- Sizing:
  * Refined element size in damage-following narrow band: h_ref = 0.0035 mm (<= l0/2 = 0.00375 mm)
  * Background element size: h_bg = 0.035 mm (10:1 ratio)
- Narrow Damage-Following Band Geometry (Mirroring Case 3):
  * Band half-width: w = 0.025 mm (~3.33 * l0, matching Case 3's 3.5 * l0 scaling)
  * Total band height: 2w = 0.050 mm
  * Ahead margin: d_ahead = 0.035 mm ahead of current crack tip
  * Wake margin: d_wake = 0.020 mm behind notch root
  * Band area: strictly < 2.5% of the plate domain across all cycles (vs 37% bounding box)
  * Follows the evolving curving crack tip with wake preservation back to notch root.
- Quality Gates Audited:
  * Gate 01: min(det(J)) > 0 (strictly positive Jacobians)
  * Gate 02: Quad element fraction >= 85.0%
  * Gate 03: Maximum aspect ratio <= 5.0
  * Gate 04: Median element size in corridor h <= l0/2 = 0.00375 mm
  * Gate 05: Total element count strictly bounded < 35,000 (empirical: 5,600 - 9,500 elements)
"""

from __future__ import print_function, division
import os
import sys
import math
import json

# Benchmark dimensions
PLATE_W = 1.0
PLATE_H = 1.0

# Notch geometry (0.5 mm at +45 deg from (0.0, 0.5))
NOTCH_START_X = 0.0
NOTCH_START_Y = 0.5
NOTCH_LEN = 0.5
NOTCH_ANGLE_RAD = math.pi / 4.0  # +45 deg
NOTCH_TIP_X = NOTCH_START_X + NOTCH_LEN * math.cos(NOTCH_ANGLE_RAD)  # 0.35355339 mm
NOTCH_TIP_Y = NOTCH_START_Y + NOTCH_LEN * math.sin(NOTCH_ANGLE_RAD)  # 0.85355339 mm

# Hole geometry
HOLE_X = 0.65
HOLE_Y = 0.65
HOLE_R = 0.10

# Material parameters
E_MOD = 210.0         # GPa (kN/mm^2)
NU = 0.30
L0 = 0.0075          # mm
L0_HALF = L0 / 2.0   # 0.00375 mm
GC = 0.0027          # kN/mm
K_RES = 1e-7
THICKNESS = 1.0      # mm

# Sizing parameters
H_REF = 0.0035       # mm (<= l0/2 = 0.00375 mm)
H_BG = 0.035         # mm (10:1 background transition)

# Narrow band parameters (mirroring Case 3 scaling)
BAND_HALF_WIDTH = 0.025  # mm (~3.33 * l0)
AHEAD_MARGIN = 0.035     # mm ahead of current crack front
WAKE_MARGIN = 0.020      # mm behind notch root

# Loading parameters
SHEAR_TO_TENSION_RATIO = 0.5  # ux = 0.5 * uy


def point_in_polygon(x, y, poly):
    """Ray-casting point-in-polygon test."""
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def build_narrow_band_polygon(tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None,
                              half_w=BAND_HALF_WIDTH, ahead_d=AHEAD_MARGIN, wake_d=WAKE_MARGIN):
    """
    Constructs a narrow damage-following band polygon hugging the crack path
    from notch tip (0.353553, 0.853553) through the tip history to the current tip,
    projecting ahead by ahead_d and preserving wake by wake_d.
    """
    tx = float(tip_x)
    ty = float(tip_y)

    pts = [(NOTCH_TIP_X, NOTCH_TIP_Y)]
    if tip_history:
        for p in tip_history:
            px, py = float(p[0]), float(p[1])
            # Only keep points strictly forward of the notch tip to prevent backward Z-folds
            if px > NOTCH_TIP_X + 0.002:
                dx = px - pts[-1][0]
                dy = py - pts[-1][1]
                if math.hypot(dx, dy) > 0.002:
                    pts.append((px, py))
    if tx > NOTCH_TIP_X + 0.002:
        dx = tx - pts[-1][0]
        dy = ty - pts[-1][1]
        if math.hypot(dx, dy) > 0.002:
            pts.append((tx, ty))

    v_notch = (math.cos(NOTCH_ANGLE_RAD), math.sin(NOTCH_ANGLE_RAD))
    dx_hole = HOLE_X - NOTCH_TIP_X
    dy_hole = HOLE_Y - NOTCH_TIP_Y
    d_hole = math.hypot(dx_hole, dy_hole)
    v_to_hole = (dx_hole / d_hole, dy_hole / d_hole)

    # Wake projection is always backward along the notch slit (prevents acute intersection with notch seam)
    p_wake = (NOTCH_TIP_X - wake_d * v_notch[0], NOTCH_TIP_Y - wake_d * v_notch[1])

    if len(pts) == 1:
        p_ahead = (NOTCH_TIP_X + ahead_d * v_to_hole[0], NOTCH_TIP_Y + ahead_d * v_to_hole[1])
        centerline = [p_wake, pts[0], p_ahead]
    else:
        last_seg_dx = pts[-1][0] - pts[-2][0]
        last_seg_dy = pts[-1][1] - pts[-2][1]
        last_seg_len = math.hypot(last_seg_dx, last_seg_dy)
        if last_seg_len > 1e-6:
            v_end = (last_seg_dx / last_seg_len, last_seg_dy / last_seg_len)
        else:
            v_end = v_to_hole

        cur_tip = pts[-1]
        dist_to_center = math.hypot(cur_tip[0] - HOLE_X, cur_tip[1] - HOLE_Y)
        dist_to_hole_boundary = dist_to_center - HOLE_R
        eff_ahead = min(ahead_d, max(0.005, dist_to_hole_boundary - 0.002)) if dist_to_hole_boundary > 0 else 0.0

        centerline = [p_wake] + pts
        if eff_ahead > 0.003:
            p_ahead = (cur_tip[0] + eff_ahead * v_end[0], cur_tip[1] + eff_ahead * v_end[1])
            centerline.append(p_ahead)

    N = len(centerline)
    normals = []
    for i in range(N):
        if i == 0:
            tx_i = centerline[1][0] - centerline[0][0]
            ty_i = centerline[1][1] - centerline[0][1]
            l_i = math.hypot(tx_i, ty_i)
            t = (tx_i / l_i, ty_i / l_i)
            n = (-t[1], t[0])
        elif i == N - 1:
            tx_i = centerline[N-1][0] - centerline[N-2][0]
            ty_i = centerline[N-1][1] - centerline[N-2][1]
            l_i = math.hypot(tx_i, ty_i)
            t = (tx_i / l_i, ty_i / l_i)
            n = (-t[1], t[0])
        else:
            t1_x = centerline[i][0] - centerline[i-1][0]
            t1_y = centerline[i][1] - centerline[i-1][1]
            l1 = math.hypot(t1_x, t1_y)
            t1 = (t1_x / l1, t1_y / l1)

            t2_x = centerline[i+1][0] - centerline[i][0]
            t2_y = centerline[i+1][1] - centerline[i][1]
            l2 = math.hypot(t2_x, t2_y)
            t2 = (t2_x / l2, t2_y / l2)

            t_avg_x = t1[0] + t2[0]
            t_avg_y = t1[1] + t2[1]
            l_avg = math.hypot(t_avg_x, t_avg_y)
            if l_avg > 1e-6:
                t_avg = (t_avg_x / l_avg, t_avg_y / l_avg)
                n = (-t_avg[1], t_avg[0])
            else:
                n = (-t1[1], t1[0])
        normals.append(n)

    left_pts = []
    right_pts = []
    for i in range(N):
        cx, cy = centerline[i]
        nx, ny = normals[i]
        lx = cx + half_w * nx
        ly = cy + half_w * ny
        rx = cx - half_w * nx
        ry = cy - half_w * ny
        left_pts.append((lx, ly))
        right_pts.append((rx, ry))

    polygon = left_pts + right_pts[::-1]

    # Compute bounding limits
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # Compute polygon area
    poly_area = 0.0
    for j in range(len(polygon)):
        x1, y1 = polygon[j]
        x2, y2 = polygon[(j + 1) % len(polygon)]
        poly_area += (x1 * y2 - x2 * y1)
    poly_area = abs(poly_area) * 0.5

    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "tip_x": tx,
        "tip_y": ty,
        "h_ref": H_REF,
        "h_bg": H_BG,
        "half_width": half_w,
        "polygon_vertices": polygon,
        "centerline": centerline,
        "polygon_area_mm2": poly_area,
        "domain_area_fraction_pct": (poly_area / (PLATE_W * PLATE_H)) * 100.0,
        "corridor_type": "NARROW_DAMAGE_FOLLOWING_BAND"
    }


def compute_corridor_spec(tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """Canonical wrapper returning the narrow-band corridor specification."""
    return build_narrow_band_polygon(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)


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
    """Computes minimum quadrature Jacobian determinant and aspect ratio."""
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
        q = 1.0 / math.sqrt(3.0)
        dets = []
        for xi, eta in [(-q, -q), (q, -q), (q, q), (-q, q)]:
            dx = [-(1 - eta) / 4.0, (1 - eta) / 4.0, (1 + eta) / 4.0, -(1 + eta) / 4.0]
            dy = [-(1 - xi) / 4.0, -(1 + xi) / 4.0, (1 + xi) / 4.0, (1 - xi) / 4.0]
            xx = sum([dx[i] * coords[i][0] for i in range(4)])
            xy = sum([dx[i] * coords[i][1] for i in range(4)])
            yx = sum([dy[i] * coords[i][0] for i in range(4)])
            yy = sum([dy[i] * coords[i][1] for i in range(4)])
            dets.append(xx * yy - xy * yx)
        min_det = min(dets)
        edges = [
            math.hypot(coords[(i + 1) % 4][0] - coords[i][0], coords[(i + 1) % 4][1] - coords[i][1])
            for i in range(4)
        ]
        min_e = min(edges) if min(edges) > 1e-12 else 1e-12
        ar = max(edges) / min_e
        return min_det, ar
    return 0.0, 1.0


def evaluate_corridor_audit(nodes, elements, elem_type_map, tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """
    Performs geometric audit of elements located in the narrow damage-following band.
    Evaluates all 5 physical mesh quality gates.
    """
    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    poly = spec["polygon_vertices"]
    corridor_elements = []
    total_quads = 0
    total_tris = 0

    min_det_global = 1e30
    max_ar_global = 0.0

    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) < 3:
            continue
        cx = sum([c[0] for c in coords]) / float(len(coords))
        cy = sum([c[1] for c in coords]) / float(len(coords))

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

        if point_in_polygon(cx, cy, poly):
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
    quad_frac = (float(total_quads) / total_elems * 100.0) if total_elems > 0 else 0.0

    h_values = [e["h"] for e in corridor_elements]
    median_h = sorted(h_values)[len(h_values) // 2] if h_values else 0.0
    max_h = max(h_values) if h_values else 0.0

    return {
        "total_elements": total_elems,
        "total_quads": total_quads,
        "total_tris": total_tris,
        "quad_percentage": quad_frac,
        "min_det_jacobian": min_det_global,
        "max_aspect_ratio": max_ar_global,
        "corridor_elements_count": len(corridor_elements),
        "median_h_corridor": median_h,
        "max_h_corridor": max_h,
        "narrow_band_area_mm2": spec["polygon_area_mm2"],
        "narrow_band_area_pct": spec["domain_area_fraction_pct"],
        "gates": {
            "gate01_positive_jacobians": min_det_global > 0.0,
            "gate02_quad_fraction_ge_85pct": quad_frac >= 85.0,
            "gate03_aspect_ratio_le_5": max_ar_global <= 5.0,
            "gate04_median_h_le_l0_half": median_h <= L0_HALF,
            "gate05_element_ceiling_35k": total_elems < 35000
        }
    }


def generate_cae_mesh(output_inp, output_audit_json, tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """
    Invokes Abaqus CAE to create the geometry, assign seam, partition narrow band,
    seed, mesh with quad-dominated free technique, and export physical mesh .inp.
    """
    try:
        from abaqus import mdb
        from abaqusConstants import TWO_D_PLANAR, DEFORMABLE_BODY, QUAD_DOMINATED, FREE, CPE4, CPE3, STANDARD, OFF, ON, ANALYSIS
        import regionToolset
        import mesh
    except ImportError:
        raise RuntimeError("Abaqus Python modules not available. Must be invoked via 'abaqus cae noGUI=...'")

    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    poly = spec["polygon_vertices"]
    print("Generating Mixed Loading (Tension + Shear) narrow-band physical mesh...")
    print("Narrow band: %d vertices, area = %.6f mm^2 (%.2f%% of plate)" % (
        len(poly), spec["polygon_area_mm2"], spec["domain_area_fraction_pct"]
    ))

    model_name = "MIXED_LOAD_INCLINED_NOTCH_HOLE_MODEL"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    # 1. Base Sketch: 1.0 x 1.0 mm outer rectangle with circular hole
    s = m.ConstrainedSketch(name="__profile__", sheetSize=5.0)
    s.rectangle(point1=(0.0, 0.0), point2=(PLATE_W, PLATE_H))
    s.CircleByCenterPerimeter(center=(HOLE_X, HOLE_Y), point1=(HOLE_X + HOLE_R, HOLE_Y))

    p = m.Part(name="MixedLoadPlate", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # 2. Partition for Notch Slit
    sp_notch = m.ConstrainedSketch(name="__notch__", sheetSize=5.0)
    sp_notch.Line(point1=(NOTCH_START_X, NOTCH_START_Y), point2=(NOTCH_TIP_X, NOTCH_TIP_Y))
    p.PartitionFaceBySketch(faces=p.faces, sketch=sp_notch)
    del m.sketches["__notch__"]

    # Assign seam to notch edge
    mid_x = 0.5 * (NOTCH_START_X + NOTCH_TIP_X)
    mid_y = 0.5 * (NOTCH_START_Y + NOTCH_TIP_Y)
    notch_edges = p.edges.findAt(((mid_x, mid_y, 0.0), ))
    if len(notch_edges) > 0:
        p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=notch_edges))
        print("Assigned seam to notch edge successfully!")

    # 3. Partition for Narrow Damage-Following Band Polygon
    sp_band = m.ConstrainedSketch(name="__band__", sheetSize=5.0)
    for j in range(len(poly)):
        sp_band.Line(point1=poly[j], point2=poly[(j + 1) % len(poly)])
    p.PartitionFaceBySketch(faces=p.faces, sketch=sp_band)
    del m.sketches["__band__"]

    # 4. Material and Section
    mat = m.Material(name="Steel")
    mat.Elastic(table=((E_MOD * 1000.0, NU), ))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=THICKNESS)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # 5. Seeding
    p.seedPart(size=H_BG, deviationFactor=0.05, minSizeFactor=0.02)

    # Find faces inside narrow band polygon
    corr_faces = []
    for f in p.faces:
        pt = f.pointOn[0]
        if point_in_polygon(pt[0], pt[1], poly):
            corr_faces.append(f)

    corr_edges = []
    seen = set()
    for f in corr_faces:
        for e_idx in f.getEdges():
            if e_idx not in seen:
                seen.add(e_idx)
                corr_edges.append(p.edges[e_idx])

    if corr_edges:
        p.seedEdgeBySize(edges=corr_edges, size=H_REF, deviationFactor=0.05, minSizeFactor=0.02, constraint=mesh.FINER)

    # Seed notch seam edge with fine seed
    seam_edges = p.edges.findAt(((mid_x, mid_y, 0.0), ))
    if len(seam_edges) > 0:
        p.seedEdgeBySize(edges=seam_edges, size=H_REF, deviationFactor=0.05, minSizeFactor=0.02, constraint=mesh.FINER)

    # 6. Mesh Controls
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces, ), elemTypes=(elem_cpe4, elem_cpe3))

    p.generateMesh()
    print("Mesh generated: %d nodes, %d elements (Corridor faces: %d)" % (
        len(p.nodes), len(p.elements), len(corr_faces)
    ))

    # 7. Write temporary input deck to extract mesh
    a = m.rootAssembly
    a.Instance(name="PART-1-1", part=p, dependent=ON)
    job_name = "TEMP_MIXED_LOAD_NARROW_PHYS"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    job.writeInput(consistencyChecking=OFF)

    # 8. Parse temporary .inp and renumber nodes/elements
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
                    if "CPE4" in u or "QUAD" in u or "DC2D4" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "TRI" in u or "DC2D3" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "QUAD"
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    if len(conn) == 4:
                        quads[eid] = conn
                    elif len(conn) == 3:
                        tris[eid] = conn

    # Renumber sequentially
    node_id_map = {}
    renumbered_nodes = {}
    for new_id, old_id in enumerate(sorted(nodes.keys()), start=1):
        node_id_map[old_id] = new_id
        renumbered_nodes[new_id] = nodes[old_id]

    renumbered_quads = {}
    elem_type_map = {}
    current_eid = 1
    for old_eid in sorted(quads.keys()):
        conn = [node_id_map[nid] for nid in quads[old_eid]]
        renumbered_quads[current_eid] = conn
        elem_type_map[current_eid] = "QUAD"
        current_eid += 1

    renumbered_tris = {}
    for old_eid in sorted(tris.keys()):
        conn = [node_id_map[nid] for nid in tris[old_eid]]
        renumbered_tris[current_eid] = conn
        elem_type_map[current_eid] = "TRI"
        current_eid += 1

    all_elements = dict(renumbered_quads)
    all_elements.update(renumbered_tris)

    # 9. Perform quality audit
    audit = evaluate_corridor_audit(
        renumbered_nodes, all_elements, elem_type_map,
        tip_x=tip_x, tip_y=tip_y, tip_history=tip_history
    )
    audit["physical_inp"] = os.path.abspath(output_inp)
    audit["tip_x"] = tip_x
    audit["tip_y"] = tip_y

    print("\n--- Physical Mesh Quality Audit ---")
    print("Total elements: %d (Quads: %d, Tris: %d, Quad %%: %.2f%%)" % (
        audit["total_elements"], audit["total_quads"], audit["total_tris"], audit["quad_percentage"]
    ))
    print("Min det(J): %.4e (Gate 01: %s)" % (
        audit["min_det_jacobian"], "PASS" if audit["gates"]["gate01_positive_jacobians"] else "FAIL"
    ))
    print("Max aspect ratio: %.3f (Gate 03: %s)" % (
        audit["max_aspect_ratio"], "PASS" if audit["gates"]["gate03_aspect_ratio_le_5"] else "FAIL"
    ))
    print("Median h in corridor: %.6f mm (Gate 04: %s)" % (
        audit["median_h_corridor"], "PASS" if audit["gates"]["gate04_median_h_le_l0_half"] else "FAIL"
    ))
    print("Element ceiling (<35k): %s" % (
        "PASS" if audit["gates"]["gate05_element_ceiling_35k"] else "FAIL"
    ))

    # 10. Write final physical mesh .inp
    with open(output_inp, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** PHYSICAL MESH DECK: Mixed Load (Tension + Shear) Narrow Band\n")
        out.write("** Crack Tip: (%.6f, %.6f) mm\n" % (tip_x, tip_y))
        out.write("** Total Elements: %d (Quads: %d, Tris: %d)\n" % (
            audit["total_elements"], audit["total_quads"], audit["total_tris"]
        ))
        out.write("** ==========================================================\n")
        out.write("*NODE\n")
        for nid, (x, y) in sorted(renumbered_nodes.items()):
            out.write("%d, %.8e, %.8e\n" % (nid, x, y))

        if renumbered_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMENTS\n")
            for eid, conn in sorted(renumbered_quads.items()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in conn)))

        if renumbered_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMENTS\n")
            for eid, conn in sorted(renumbered_tris.items()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in conn)))

        out.write("*ELSET, ELSET=ALL_ELEMENTS\n")
        if renumbered_quads:
            out.write("QUAD_ELEMENTS\n")
        if renumbered_tris:
            out.write("TRI_ELEMENTS\n")

    # 11. Write audit JSON
    with open(output_audit_json, "w") as jf:
        json.dump(audit, jf, indent=2)
    print("Physical mesh written: %s" % output_inp)
    print("Audit JSON written: %s" % output_audit_json)

    # Clean up temp files
    for ext in [".inp", ".log", ".prt", ".sim", ".rpy"]:
        fn = job_name + ext
        if os.path.exists(fn):
            try:
                os.remove(fn)
            except Exception:
                pass


def parse_cli_args():
    """Extracts target output path, audit path, tip_x, tip_y, and tip_history from sys.argv."""
    raw_args = sys.argv[1:]
    user_args = []
    skip_next = False
    history_arg = None
    for i, a in enumerate(raw_args):
        if skip_next:
            skip_next = False
            continue
        if a in ("-cae", "-noGUI", "--"):
            continue
        if a in ("-tmpdir", "-lmlog"):
            skip_next = True
            continue
        if a == "--history":
            if i + 1 < len(raw_args):
                history_arg = raw_args[i + 1]
                skip_next = True
            continue
        if a.endswith(".py"):
            continue
        user_args.append(a)

    out_inp = "PK_METHOD_C_MIXED_LOAD_COARSE_PHYS.inp"
    out_audit = "PK_METHOD_C_MIXED_LOAD_COARSE_PHYS_audit.json"
    tip_x = NOTCH_TIP_X
    tip_y = NOTCH_TIP_Y
    tip_history = []

    if len(user_args) >= 1 and not user_args[0].startswith("-"):
        out_inp = user_args[0]
    if len(user_args) >= 2 and not user_args[1].startswith("-"):
        out_audit = user_args[1]
    if len(user_args) >= 3:
        try:
            tip_x = float(user_args[2])
        except ValueError:
            pass
    if len(user_args) >= 4:
        try:
            tip_y = float(user_args[3])
        except ValueError:
            pass
    if len(user_args) >= 5 and not history_arg:
        history_arg = user_args[4]

    if history_arg:
        if os.path.exists(history_arg):
            try:
                with open(history_arg, "r") as f:
                    tip_history = json.load(f)
            except Exception as err:
                print("Warning: failed to read history file %s: %s" % (history_arg, err))
        else:
            try:
                tip_history = json.loads(history_arg)
            except Exception:
                pass

    return out_inp, out_audit, tip_x, tip_y, tip_history


if __name__ == "__main__":
    out_inp, out_audit, tx, ty, th = parse_cli_args()
    print("Mixed-Load Mesh Generator CLI: inp=%s, audit=%s, tip=(%.4f, %.4f), history_len=%d" % (
        out_inp, out_audit, tx, ty, len(th) if th else 0
    ))
    generate_cae_mesh(out_inp, out_audit, tip_x=tx, tip_y=ty, tip_history=th)
