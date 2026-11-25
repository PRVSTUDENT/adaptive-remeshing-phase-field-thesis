# -*- coding: utf-8 -*-
"""
models/novel_inclined_notch_hole/generate_novel_inclined_notch_hole_mesh.py
==========================================================================
Task: METHOD-C-NOVEL-INCLINED-NOTCH-HOLE
Goal: METHOD_C_MODE2_LPANEL_V1
Correlation: HND-METHOD-C-MODE2-LPANEL-014

Generates and audits the adaptive corridor physical mesh for the Novel Complex Problem:
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
  * Refined element size in damage-following corridor: h_ref = 0.0035 mm (<= l0/2 = 0.00375 mm)
  * Background element size: h_bg = 0.035 mm
- Dynamic Damage-Following Corridor:
  * Follows the evolving curving crack tip with wake preservation back to the notch tip.
  * Box bounds:
    x_min = max(0.0, min(0.353553, tip_x) - 0.06)
    x_max = min(1.0, max(0.353553, tip_x) + 0.10)
    y_min = max(0.0, min(0.853553, tip_y) - 0.08)
    y_max = min(1.0, max(0.853553, tip_y) + 0.08)
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

H_REF = 0.0035       # mm (<= l0/2 = 0.00375 mm)
H_BG = 0.035         # mm (H_BG / H_REF = 10.0 transition)


def compute_corridor_spec(tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """
    Computes dynamic damage-following corridor specification.
    Preserves wake back to initial notch tip (0.353553, 0.853553) and extends
    ahead and transversely around current crack tip (tip_x, tip_y).
    """
    tx = float(tip_x)
    ty = float(tip_y)

    xs = [NOTCH_TIP_X, tx]
    ys = [NOTCH_TIP_Y, ty]
    if tip_history:
        for p in tip_history:
            xs.append(float(p[0]))
            ys.append(float(p[1]))

    ahead_x = 0.10
    trans_y = 0.08
    wake_x = 0.06

    x_min = max(0.0, min(xs) - wake_x)
    x_max = min(1.0, max(xs) + ahead_x)
    y_min = max(0.0, min(ys) - trans_y)
    y_max = min(1.0, max(ys) + trans_y)

    # Avoid partition lines slicing across the stress-concentrating circular hole
    # Hole domain is [0.55, 0.75] x [0.55, 0.75] (center 0.65, 0.65, radius 0.10).
    # When the corridor reaches near the hole, expand the box to completely enclose
    # the circular hole so partition boundaries never intersect the circular arc.
    hole_xmin = HOLE_X - HOLE_R
    hole_xmax = HOLE_X + HOLE_R
    hole_ymin = HOLE_Y - HOLE_R
    hole_ymax = HOLE_Y + HOLE_R
    margin = 0.03
    if x_max >= (hole_xmin - margin) and y_min <= (hole_ymax + margin):
        x_max = min(1.0, max(x_max, hole_xmax + margin))
        y_min = max(0.0, min(y_min, hole_ymin - margin))

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


def evaluate_corridor_audit(nodes, elements, elem_type_map, tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y):
    """Performs geometric audit of elements located in the adaptive corridor."""
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


def generate_novel_physical_mesh(out_phys_inp, tip_x=NOTCH_TIP_X, tip_y=NOTCH_TIP_Y, tip_history=None):
    """
    Generates the Novel Problem adaptive corridor physical mesh using Abaqus CAE.
    Must be executed in Abaqus environment (e.g. abaqus cae noGUI=...).
    """
    try:
        from abaqus import mdb
        from abaqusConstants import TWO_D_PLANAR, DEFORMABLE_BODY, QUAD_DOMINATED, FREE, CPE4, CPE3, STANDARD, OFF, ON, ANALYSIS
        import regionToolset
        import mesh
    except ImportError:
        raise RuntimeError("Abaqus Python modules not available. Must be invoked via 'abaqus cae noGUI=...'")

    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y, tip_history=tip_history)
    print("Generating Novel Inclined Notch + Hole adaptive physical mesh...")
    print("Corridor: x in [%.4f, %.4f] mm, y in [%.4f, %.4f] mm" % (
        spec["x_min"], spec["x_max"], spec["y_min"], spec["y_max"]
    ))

    model_name = "NOVEL_INCLINED_NOTCH_HOLE_MODEL"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    # 1. Base Sketch: 1.0 x 1.0 mm outer rectangle
    s = m.ConstrainedSketch(name="__profile__", sheetSize=5.0)
    s.rectangle(point1=(0.0, 0.0), point2=(PLATE_W, PLATE_H))
    # Circular hole at (0.65, 0.65), radius 0.10
    s.CircleByCenterPerimeter(center=(HOLE_X, HOLE_Y), point1=(HOLE_X + HOLE_R, HOLE_Y))

    p = m.Part(name="NovelPlate", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # 2. Partition for Notch Slit
    sp_notch = m.ConstrainedSketch(name="__notch__", sheetSize=5.0)
    sp_notch.Line(point1=(NOTCH_START_X, NOTCH_START_Y), point2=(NOTCH_TIP_X, NOTCH_TIP_Y))
    p.PartitionFaceBySketch(faces=p.faces, sketch=sp_notch)
    del m.sketches["__notch__"]

    # Find the notch edge and assign seam
    mid_x = 0.5 * (NOTCH_START_X + NOTCH_TIP_X)
    mid_y = 0.5 * (NOTCH_START_Y + NOTCH_TIP_Y)
    notch_edges = p.edges.findAt(((mid_x, mid_y, 0.0), ))
    if len(notch_edges) > 0:
        p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=notch_edges))
        print("Assigned seam to notch edge successfully!")

    # 3. Partition for Dynamic Adaptive Corridor
    sp_corr = m.ConstrainedSketch(name="__corridor__", sheetSize=5.0)
    sp_corr.rectangle(point1=(spec["x_min"], spec["y_min"]), point2=(spec["x_max"], spec["y_max"]))
    p.PartitionFaceBySketch(faces=p.faces, sketch=sp_corr)
    del m.sketches["__corridor__"]

    # 4. Material and Section
    mat = m.Material(name="Steel")
    mat.Elastic(table=((E_MOD * 1000.0, NU), ))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=THICKNESS)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # 5. Seeding
    p.seedPart(size=H_BG, deviationFactor=0.05, minSizeFactor=0.02)

    # Find faces inside corridor
    corr_faces = []
    x_min = spec["x_min"]
    x_max = spec["x_max"]
    y_min = spec["y_min"]
    y_max = spec["y_max"]

    for f in p.faces:
        pt = f.pointOn[0]
        if (x_min - 1e-4 <= pt[0] <= x_max + 1e-4) and (y_min - 1e-4 <= pt[1] <= y_max + 1e-4):
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
    print("Mesh generated: %d nodes, %d elements" % (len(p.nodes), len(p.elements)))

    # 7. Write temporary input deck to extract mesh
    a = m.rootAssembly
    a.Instance(name="PART-1-1", part=p, dependent=ON)
    job_name = "TEMP_NOVEL_CORRIDOR_PHYS"
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

    # 9. Write final physical mesh .inp
    with open(out_phys_inp, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** Physical Mesh for Method C Novel Inclined Notch + Hole\n")
        out.write("** Model: %s\n" % os.path.basename(out_phys_inp).replace(".inp", ""))
        out.write("** Tip: (%.6f, %.6f) mm | Corridor: [%.4f, %.4f] x [%.4f, %.4f] mm\n" % (
            spec["tip_x"], spec["tip_y"], spec["x_min"], spec["x_max"], spec["y_min"], spec["y_max"]
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

    audit = evaluate_corridor_audit(renumbered_nodes, all_elems, elem_type_map, tip_x=tip_x, tip_y=tip_y)
    audit_path = out_phys_inp.replace(".inp", "_audit.json")
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)
    print("Audit written to: %s" % audit_path)
    print("Quality Gates: %s" % str(audit["gates"]))
    return audit


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

    out_target = "PK_METHOD_C_NOVEL_COARSE_PHYS.inp"
    tip_x = NOTCH_TIP_X
    tip_y = NOTCH_TIP_Y

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
    print("Novel Mesh Generator CLI: target=%s, tip=(%.4f, %.4f)" % (out_target, tip_x, tip_y))
    generate_novel_physical_mesh(out_target, tip_x=tip_x, tip_y=tip_y)
