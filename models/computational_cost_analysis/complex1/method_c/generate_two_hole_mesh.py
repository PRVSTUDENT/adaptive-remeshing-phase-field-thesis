# -*- coding: utf-8 -*-
"""
models/complex_two_hole/generate_two_hole_mesh.py
=================================================
Task: METHOD-C-COMPLEX-MODELS
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-001

Generates and audits the narrow damage-following band physical mesh for Problem 1:
- Benchmark: Inclined Notch + Two Holes in Series
  * Domain: 1.0 x 1.0 mm square plate: [0.0, 1.0] x [0.0, 1.0] mm
  * Inclined Notch: 0.5 mm edge notch at +45 deg from (0.0, 0.5) to (0.35355339, 0.85355339) mm
  * Hole 1: center (0.65, 0.65) mm, radius R1 = 0.10 mm
  * Hole 2: center (0.87, 0.62) mm, radius R2 = 0.06 mm
  * Ligament between Hole 1 and Hole 2: ~0.0620 mm
- Material & Physics:
  * E = 210.0 GPa (210.0 kN/mm^2)
  * nu = 0.30
  * l0 = 0.0075 mm (l0 / 2 = 0.00375 mm)
  * Gc = 0.0027 kN/mm (2.7 N/mm)
  * k_res = 1.0e-7
  * Thickness = 1.0 mm
- Discretization & Sizing:
  * Refined element size inside narrow bands: h_ref = 0.0035 mm (<= l0/2 = 0.00375 mm)
  * Background element size: h_bg = 0.035 mm (10:1 ratio)
  * Narrow Band Half-Width: w = 0.025 mm (~3.33 * l0)
  * Primary Band: follows Crack 1 from notch root to Hole 1
  * Secondary Band: covers inter-hole ligament between Hole 1 and Hole 2
  * Total refined area < 2.5% of plate domain
- Quality Gates Audited:
  * Gate 01: min(det(J)) > 0 (strictly positive Jacobians)
  * Gate 02: Quad element fraction >= 85.0%
  * Gate 03: Maximum aspect ratio <= 5.0
  * Gate 04: Median element size in corridor h <= l0/2 = 0.00375 mm
  * Gate 05: Total element count strictly bounded < 35,000
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

# Hole 1 geometry
HOLE1_X = 0.65
HOLE1_Y = 0.65
HOLE1_R = 0.10

# Hole 2 geometry
HOLE2_X = 0.87
HOLE2_Y = 0.62
HOLE2_R = 0.06

# Ligament between Hole 1 and Hole 2
DX_HOLES = HOLE2_X - HOLE1_X  # 0.22 mm
DY_HOLES = HOLE2_Y - HOLE1_Y  # -0.03 mm
DIST_HOLES_CENTERS = math.hypot(DX_HOLES, DY_HOLES)  # ~0.222036 mm
INTER_HOLE_LIGAMENT = DIST_HOLES_CENTERS - (HOLE1_R + HOLE2_R)  # ~0.062036 mm

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

# Narrow band parameters
BAND_HALF_WIDTH = 0.025  # mm (~3.33 * l0)
AHEAD_MARGIN = 0.035     # mm ahead of current crack front
WAKE_MARGIN = 0.020      # mm behind notch root


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


def build_primary_narrow_band_polygon(tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None,
                                      half_w=BAND_HALF_WIDTH, ahead_d=AHEAD_MARGIN, wake_d=WAKE_MARGIN):
    """
    Constructs a narrow damage-following band polygon hugging Crack 1 from notch tip
    (0.353553, 0.853553) through the tip history towards Hole 1 (0.65, 0.65).
    """
    tx = float(tip_x)
    ty = float(tip_y)

    pts = [(NOTCH_TIP_X, NOTCH_TIP_Y)]
    if tip_history:
        for p in tip_history:
            px, py = float(p[0]), float(p[1])
            dx = px - pts[-1][0]
            dy = py - pts[-1][1]
            if math.hypot(dx, dy) > 0.002:
                pts.append((px, py))
    dx = tx - pts[-1][0]
    dy = ty - pts[-1][1]
    if math.hypot(dx, dy) > 0.002:
        pts.append((tx, ty))

    v_notch = (math.cos(NOTCH_ANGLE_RAD), math.sin(NOTCH_ANGLE_RAD))
    dx_hole = HOLE1_X - NOTCH_TIP_X
    dy_hole = HOLE1_Y - NOTCH_TIP_Y
    d_hole = math.hypot(dx_hole, dy_hole)
    v_to_hole = (dx_hole / d_hole, dy_hole / d_hole)

    if len(pts) == 1:
        p_wake = (NOTCH_TIP_X - wake_d * v_notch[0], NOTCH_TIP_Y - wake_d * v_notch[1])
        p_ahead = (NOTCH_TIP_X + ahead_d * v_to_hole[0], NOTCH_TIP_Y + ahead_d * v_to_hole[1])
        centerline = [p_wake, pts[0], p_ahead]
    else:
        # Collinear backward wake projection along initial crack tangent
        v0_x = pts[1][0] - pts[0][0]
        v0_y = pts[1][1] - pts[0][1]
        l0 = math.hypot(v0_x, v0_y)
        v0 = (v0_x / l0, v0_y / l0) if l0 > 1e-6 else v_to_hole
        p_wake = (pts[0][0] - wake_d * v0[0], pts[0][1] - wake_d * v0[1])

        last_seg_dx = pts[-1][0] - pts[-2][0]
        last_seg_dy = pts[-1][1] - pts[-2][1]
        last_seg_len = math.hypot(last_seg_dx, last_seg_dy)
        if last_seg_len > 1e-6:
            v_end = (last_seg_dx / last_seg_len, last_seg_dy / last_seg_len)
        else:
            v_end = v_to_hole

        cur_tip = pts[-1]
        dist_to_center = math.hypot(cur_tip[0] - HOLE1_X, cur_tip[1] - HOLE1_Y)
        dist_to_hole_boundary = dist_to_center - HOLE1_R
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
        left_pts.append((cx + half_w * nx, cy + half_w * ny))
        right_pts.append((cx - half_w * nx, cy - half_w * ny))

    polygon = left_pts + right_pts[::-1]
    poly_area = 0.0
    for j in range(len(polygon)):
        x1, y1 = polygon[j]
        x2, y2 = polygon[(j + 1) % len(polygon)]
        poly_area += (x1 * y2 - x2 * y1)
    poly_area = abs(poly_area) * 0.5

    return {
        "polygon_vertices": polygon,
        "centerline": centerline,
        "area_mm2": poly_area,
        "tip_x": tx,
        "tip_y": ty
    }


def build_secondary_narrow_band_polygon(half_w=BAND_HALF_WIDTH):
    """
    Constructs the secondary narrow band polygon covering the inter-hole ligament
    between Hole 1 (0.65, 0.65) R=0.10 and Hole 2 (0.87, 0.62) R=0.06.
    Centerline runs from x=0.74 (Hole 1 right edge) to x=0.94 (through Hole 2).
    """
    p_start = (0.74, 0.65)
    p_end = (0.94, 0.61)

    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    L = math.hypot(dx, dy)
    tx, ty = dx / L, dy / L
    nx, ny = -ty, tx  # Normal vector

    # 4 corners of rectangle
    c1 = (p_start[0] + half_w * nx, p_start[1] + half_w * ny)
    c2 = (p_end[0] + half_w * nx, p_end[1] + half_w * ny)
    c3 = (p_end[0] - half_w * nx, p_end[1] - half_w * ny)
    c4 = (p_start[0] - half_w * nx, p_start[1] - half_w * ny)

    polygon = [c1, c2, c3, c4]
    poly_area = L * (2.0 * half_w)

    return {
        "polygon_vertices": polygon,
        "centerline": [p_start, p_end],
        "area_mm2": poly_area
    }


def compute_corridor_spec(tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """Returns combined corridor specification for Problem 1 (Primary + Secondary Bands)."""
    p_band = build_primary_narrow_band_polygon(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    s_band = build_secondary_narrow_band_polygon()
    total_area = p_band["area_mm2"] + s_band["area_mm2"]
    frac_pct = (total_area / (PLATE_W * PLATE_H)) * 100.0

    return {
        "primary_band": p_band,
        "secondary_band": s_band,
        "tip_x": p_band["tip_x"],
        "tip_y": p_band["tip_y"],
        "h_ref": H_REF,
        "h_bg": H_BG,
        "half_width": BAND_HALF_WIDTH,
        "total_refined_area_mm2": total_area,
        "domain_area_fraction_pct": frac_pct,
        "corridor_type": "TWO_HOLE_DUAL_NARROW_BAND"
    }


def compute_element_area_and_h(coords):
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
    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    poly1 = spec["primary_band"]["polygon_vertices"]
    poly2 = spec["secondary_band"]["polygon_vertices"]

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

        if point_in_polygon(cx, cy, poly1) or point_in_polygon(cx, cy, poly2):
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


def generate_two_hole_physical_mesh(out_phys_inp, tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """
    Generates Problem 1 (Inclined Notch + Two Holes in Series) physical mesh using Abaqus CAE.
    Must be executed via Abaqus CAE: 'abaqus cae noGUI=...'
    """
    try:
        from abaqus import mdb
        from abaqusConstants import TWO_D_PLANAR, DEFORMABLE_BODY, QUAD_DOMINATED, FREE, CPE4, CPE3, STANDARD, OFF, ON, ANALYSIS
        import regionToolset
        import mesh
    except ImportError:
        raise RuntimeError("Abaqus Python modules not available. Must be invoked via 'abaqus cae noGUI=...'")

    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    poly1 = spec["primary_band"]["polygon_vertices"]
    poly2 = spec["secondary_band"]["polygon_vertices"]

    print("Generating Problem 1: Inclined Notch + Two Holes physical mesh...")
    print("Primary Band: %d vertices, area = %.6f mm^2" % (len(poly1), spec["primary_band"]["area_mm2"]))
    print("Secondary Band: %d vertices, area = %.6f mm^2" % (len(poly2), spec["secondary_band"]["area_mm2"]))
    print("Total refined area = %.6f mm^2 (%.2f%% of plate)" % (
        spec["total_refined_area_mm2"], spec["domain_area_fraction_pct"]
    ))

    model_name = "TWO_HOLE_MODEL"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    # 1. Base Sketch: 1.0 x 1.0 mm plate with Hole 1 and Hole 2 cut out
    s = m.ConstrainedSketch(name="__profile__", sheetSize=5.0)
    s.rectangle(point1=(0.0, 0.0), point2=(PLATE_W, PLATE_H))
    s.CircleByCenterPerimeter(center=(HOLE1_X, HOLE1_Y), point1=(HOLE1_X + HOLE1_R, HOLE1_Y))
    s.CircleByCenterPerimeter(center=(HOLE2_X, HOLE2_Y), point1=(HOLE2_X + HOLE2_R, HOLE2_Y))

    p = m.Part(name="TwoHolePlate", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
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

    # 3. Partition for Primary Narrow Band Polygon
    sp_band1 = m.ConstrainedSketch(name="__band1__", sheetSize=5.0)
    for j in range(len(poly1)):
        sp_band1.Line(point1=poly1[j], point2=poly1[(j + 1) % len(poly1)])
    p.PartitionFaceBySketch(faces=p.faces, sketch=sp_band1)
    del m.sketches["__band1__"]

    # 4. Partition for Secondary Narrow Band Polygon (Inter-hole band)
    sp_band2 = m.ConstrainedSketch(name="__band2__", sheetSize=5.0)
    for j in range(len(poly2)):
        sp_band2.Line(point1=poly2[j], point2=poly2[(j + 1) % len(poly2)])
    p.PartitionFaceBySketch(faces=p.faces, sketch=sp_band2)
    del m.sketches["__band2__"]

    # 5. Material and Section
    mat = m.Material(name="Steel")
    mat.Elastic(table=((E_MOD * 1000.0, NU), ))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=THICKNESS)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # 6. Seeding
    p.seedPart(size=H_BG, deviationFactor=0.05, minSizeFactor=0.05)

    # Find faces inside either narrow band polygon
    corr_faces = []
    for f in p.faces:
        pt = f.pointOn[0]
        if point_in_polygon(pt[0], pt[1], poly1) or point_in_polygon(pt[0], pt[1], poly2):
            corr_faces.append(f)

    corr_edges = []
    seen = set()
    for f in corr_faces:
        for e_idx in f.getEdges():
            if e_idx not in seen:
                seen.add(e_idx)
                corr_edges.append(p.edges[e_idx])

    if corr_edges:
        p.seedEdgeBySize(edges=corr_edges, size=H_REF, deviationFactor=0.05, minSizeFactor=0.05, constraint=mesh.FINER)

    # Seed notch seam edge with fine seed
    seam_edges = p.edges.findAt(((mid_x, mid_y, 0.0), ))
    if len(seam_edges) > 0:
        p.seedEdgeBySize(edges=seam_edges, size=H_REF, deviationFactor=0.05, minSizeFactor=0.05, constraint=mesh.FINER)

    # Seed left boundary edges with smooth transition to prevent corner aspect ratio spikes
    left_edge1 = p.edges.findAt(((0.0, 0.25, 0.0), ))
    left_edge2 = p.edges.findAt(((0.0, 0.75, 0.0), ))
    if len(left_edge1) > 0 and len(left_edge2) > 0:
        p.seedEdgeByBias(biasMethod=SINGLE, end2Edges=left_edge1, minSize=H_REF * 2, maxSize=H_BG, constraint=mesh.FINER)
        p.seedEdgeByBias(biasMethod=SINGLE, end1Edges=left_edge2, minSize=H_REF * 2, maxSize=H_BG, constraint=mesh.FINER)

    # 7. Mesh Controls
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces, ), elemTypes=(elem_cpe4, elem_cpe3))

    p.generateMesh()
    print("Mesh generated: %d nodes, %d elements (Corridor faces: %d)" % (
        len(p.nodes), len(p.elements), len(corr_faces)
    ))

    # 8. Write temporary input deck to extract mesh
    a = m.rootAssembly
    a.Instance(name="PART-1-1", part=p, dependent=ON)
    job_name = "TEMP_TWO_HOLE_PHYS"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    job.writeInput(consistencyChecking=OFF)

    # 9. Parse temporary .inp and renumber nodes/elements
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
    sorted_old_nids = sorted(nodes.keys())
    for new_nid, old_nid in enumerate(sorted_old_nids, start=1):
        node_map[old_nid] = new_nid

    renumbered_nodes = {node_map[old]: coords for old, coords in nodes.items()}

    renumbered_quads = {}
    new_eid = 1
    for old_eid in sorted(quads.keys()):
        renumbered_quads[new_eid] = [node_map[old_nid] for old_nid in quads[old_eid]]
        new_eid += 1

    renumbered_tris = {}
    for old_eid in sorted(tris.keys()):
        renumbered_tris[new_eid] = [node_map[old_nid] for old_nid in tris[old_eid]]
        new_eid += 1

    # Clean up temporary Abaqus job files
    for ext in [".inp", ".log"]:
        tpath = job_name + ext
        if os.path.exists(tpath):
            try:
                os.remove(tpath)
            except Exception:
                pass

    # 10. Write final physical mesh .inp
    with open(out_phys_inp, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** Physical Mesh for Problem 1: Two Holes in Series\n")
        out.write("** Model: %s\n" % os.path.basename(out_phys_inp).replace(".inp", ""))
        out.write("** Tip: (%.6f, %.6f) mm | Total Refined Area: %.6f mm^2 (%.2f%%)\n" % (
            spec["tip_x"], spec["tip_y"], spec["total_refined_area_mm2"], spec["domain_area_fraction_pct"]
        ))
        out.write("** Elements: %d total (%d quads, %d tris), Nodes: %d\n" % (
            len(renumbered_quads) + len(renumbered_tris), len(renumbered_quads), len(renumbered_tris), len(renumbered_nodes)
        ))
        out.write("** ==========================================================\n")
        out.write("*NODE\n")
        for nid in sorted(renumbered_nodes.keys()):
            c = renumbered_nodes[nid]
            out.write("%d, %.8e, %.8e\n" % (nid, c[0], c[1]))

        if renumbered_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMENTS\n")
            for eid in sorted(renumbered_quads.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in renumbered_quads[eid])))

        if renumbered_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMENTS\n")
            for eid in sorted(renumbered_tris.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in renumbered_tris[eid])))

        out.write("*ELSET, ELSET=ALL_ELEMENTS\n")
        if renumbered_quads and renumbered_tris:
            out.write("QUAD_ELEMENTS, TRI_ELEMENTS\n")
        elif renumbered_quads:
            out.write("QUAD_ELEMENTS\n")
        else:
            out.write("TRI_ELEMENTS\n")

    print("Wrote physical mesh: %s" % out_phys_inp)

    elem_type_map = {}
    for eid in renumbered_quads:
        elem_type_map[eid] = "QUAD"
    for eid in renumbered_tris:
        elem_type_map[eid] = "TRI"

    all_elems = dict(renumbered_quads)
    all_elems.update(renumbered_tris)

    audit = evaluate_corridor_audit(renumbered_nodes, all_elems, elem_type_map,
                                    tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    audit_path = out_phys_inp.replace(".inp", "_audit.json")
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)
    print("Audit written to: %s" % audit_path)
    print("Quality Gates: %s" % str(audit["gates"]))
    return audit


def parse_cli_args():
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

    out_target = "PK_METHOD_C_TWO_HOLE_COARSE_PHYS.inp"
    tip_x = NOTCH_TIP_X
    tip_y = NOTCH_TIP_Y
    tip_history = []

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
    if len(user_args) >= 4 and not history_arg:
        history_arg = user_args[3]

    if history_arg:
        try:
            tip_history = json.loads(history_arg)
        except Exception:
            pass

    return out_target, tip_x, tip_y, tip_history


if __name__ == "__main__":
    out_target, tip_x, tip_y, tip_history = parse_cli_args()
    generate_two_hole_physical_mesh(out_target, tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
