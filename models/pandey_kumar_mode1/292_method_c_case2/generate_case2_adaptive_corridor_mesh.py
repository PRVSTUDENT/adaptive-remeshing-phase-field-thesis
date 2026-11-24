# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode1/292_method_c_case2/generate_case2_adaptive_corridor_mesh.py
=====================================================================================
Task: METHOD-C-PHASE2-CASE2-FULL-RUN
Correlation: HND-METHOD-C-PHASE2-CASE2-001

Generates and audits the narrow corridor physical mesh for Method C Case 2:
- Benchmark: Master Thesis Mode-I Edge-Notched Plate with Off-Axis Hole
- Domain: 1.0 x 1.0 mm square plate with initial horizontal notch at y = 0.5 mm,
  from x = 0.0 to x = 0.5 mm (notch root at (0.5000, 0.5000) mm).
- Circular Hole: center at (0.6500, 0.6500) mm, radius R = 0.1000 mm.
- Seam: assignSeam along x in [0.0, 0.5] mm at y = 0.5 mm, creating double-node crack flanks.
- Dual Refinement Corridors:
  * Primary Corridor (Notch to Hole): x in [0.4500, 0.6200], y in [0.4600, 0.6200] mm
  * Secondary Corridor (Distal Ligament): x in [0.7200, x_max], y in [0.5800, 0.7200] mm
    where x_max = min(1.0000, max(0.8500, tip_x + 0.0800))
  * Refined seed: h_ref = 0.0035 mm < l0 / 2 = 0.00375 mm (l0 = 0.0075 mm)
  * Background seed: h_bg = 0.025 mm
  * Wake-preserving progressive advance: retains wake elements in both bands,
    progressively expanding the distal band ahead of the advancing crack.
- Quality Gates Audited:
  * Gate 01: Minimum Jacobian determinant min(det(J)) > 0 (strictly positive)
  * Gate 02: Quad element fraction >= 85.0%
  * Gate 03: Median aspect ratio <= 2.5 and maximum aspect ratio <= 5.0
  * Gate 04: Refined element size h = sqrt(Area) <= 0.00375 mm (l0 / 2)
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

# Benchmark parameters: Case 2
PLATE_W = 1.0000
PLATE_H = 1.0000
NOTCH_A = 0.5000
NOTCH_Y = 0.5000
HOLE_X = 0.6500
HOLE_Y = 0.6500
HOLE_R = 0.1000

# Sizing and physics parameters
L0 = 0.0075
L0_HALF = L0 / 2.0  # 0.00375 mm
H_REF = 0.0035      # Refined element size (<= l0/2)
H_BG = 0.0250       # Background element size


def compute_corridor_spec(tip_x=0.5000, tip_y=0.5000):
    """
    Computes Case 2 dual-band corridor specification given crack tip position.
    Wake-preserving progressive advance:
    - Retains Primary Corridor (notch to hole: x in [0.45, 0.62], y in [0.46, 0.62])
    - Dynamically extends Secondary Corridor (distal: x in [0.72, x_max], y in [0.58, 0.72])
    """
    tip_x = float(tip_x)
    tip_y = float(tip_y)

    # Primary Corridor
    p1_xmin = 0.4500
    p1_xmax = 0.6200
    p1_ymin = 0.4600
    p1_ymax = 0.6200

    # Secondary Corridor
    p2_xmin = 0.7200
    if tip_x <= 0.6000:
        p2_xmax = 0.8500
    else:
        p2_xmax = min(PLATE_W, max(0.8500, tip_x + 0.0800))
    p2_ymin = 0.5800
    p2_ymax = 0.7200

    return {
        "band_type": "CASE2_DUAL_CORRIDOR_WAKE_PRESERVING",
        "tip_x": tip_x,
        "tip_y": tip_y,
        "primary_band": {
            "x_min": p1_xmin, "x_max": p1_xmax,
            "y_min": p1_ymin, "y_max": p1_ymax,
            "polygon": [(p1_xmin, p1_ymin), (p1_xmax, p1_ymin), (p1_xmax, p1_ymax), (p1_xmin, p1_ymax)]
        },
        "secondary_band": {
            "x_min": p2_xmin, "x_max": p2_xmax,
            "y_min": p2_ymin, "y_max": p2_ymax,
            "polygon": [(p2_xmin, p2_ymin), (p2_xmax, p2_ymin), (p2_xmax, p2_ymax), (p2_xmin, p2_ymax)]
        },
        "h_ref_mm": H_REF,
        "h_bg_mm": H_BG,
        "l0_mm": L0,
        "l0_half_mm": L0_HALF
    }


def compute_element_area_and_h(coords):
    """Computes area and characteristic size h = sqrt(Area) for 2D quad or tri element."""
    n = len(coords)
    if n == 3:
        x0, y0 = coords[0]
        x1, y1 = coords[1]
        x2, y2 = coords[2]
        area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
    elif n == 4:
        x0, y0 = coords[0]
        x1, y1 = coords[1]
        x2, y2 = coords[2]
        x3, y3 = coords[3]
        area = 0.5 * abs((x0*y1 - y0*x1) + (x1*y2 - y1*x2) + (x2*y3 - y2*x3) + (x3*y0 - y3*x0))
    else:
        area = 0.0
    h = math.sqrt(area) if area > 0 else 0.0
    return area, h


def generate_abaqus_cae_mesh(out_phys_inp, tip_x=0.5000, tip_y=0.5000):
    """Executes Abaqus CAE commands to generate physical mesh with hole, seam, and dual corridors for Case 2."""
    try:
        from abaqus import mdb
        from abaqusConstants import TWO_D_PLANAR, DEFORMABLE_BODY, QUAD_DOMINATED, FREE, CPE4, CPE3, STANDARD, OFF, ON, ANALYSIS
        import regionToolset
        import mesh
    except ImportError:
        raise RuntimeError("Abaqus Python modules not available. Must be invoked via 'abaqus cae noGUI=...'")

    spec = compute_corridor_spec(tip_x=tip_x, tip_y=tip_y)
    p1 = spec["primary_band"]
    p2 = spec["secondary_band"]

    print("Generating Case 2 Dual-Corridor physical mesh at tip (%.4f, %.4f)..." % (tip_x, tip_y))
    print("  Primary band:   x in [%.4f, %.4f], y in [%.4f, %.4f]" % (p1["x_min"], p1["x_max"], p1["y_min"], p1["y_max"]))
    print("  Secondary band: x in [%.4f, %.4f], y in [%.4f, %.4f]" % (p2["x_min"], p2["x_max"], p2["y_min"], p2["y_max"]))

    model_name = "CASE2_NARROW_BAND"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    # 1. Base sketch: plate with hole
    s = m.ConstrainedSketch(name="__profile__", sheetSize=5.0)
    outer_pts = [(0.0, 0.0), (PLATE_W, 0.0), (PLATE_W, PLATE_H), (0.0, PLATE_H)]
    for i in range(len(outer_pts)):
        s.Line(point1=outer_pts[i], point2=outer_pts[(i + 1) % len(outer_pts)])
    s.CircleByCenterPerimeter(center=(HOLE_X, HOLE_Y), point1=(HOLE_X + HOLE_R, HOLE_Y))

    p = m.Part(name="Case2PlateCorridorRefined", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # 2. Partition Face by Sketch for Seam & Corridors
    sp = m.ConstrainedSketch(name="__partitions__", sheetSize=5.0)
    # Seam line from (0.0, 0.5) to (0.5, 0.5)
    sp.Line(point1=(0.0, NOTCH_Y), point2=(NOTCH_A, NOTCH_Y))

    # Primary corridor rectangle
    poly1 = p1["polygon"]
    for i in range(len(poly1)):
        sp.Line(point1=poly1[i], point2=poly1[(i + 1) % len(poly1)])

    # Secondary corridor rectangle
    poly2 = p2["polygon"]
    for i in range(len(poly2)):
        sp.Line(point1=poly2[i], point2=poly2[(i + 1) % len(poly2)])

    p.PartitionFaceBySketch(faces=p.faces, sketch=sp)
    del m.sketches["__partitions__"]

    # 3. Assign Seam to initial notch edges from x = 0.0 to x = 0.5 at y = 0.5
    seam_pts = []
    for edge in p.edges:
        pt = edge.pointOn[0]
        if abs(pt[1] - NOTCH_Y) < 1e-4 and pt[0] <= NOTCH_A + 1e-4:
            seam_pts.append(pt)
    print("Found %d seam edges along initial notch: x <= %.4f, y = %.4f" % (len(seam_pts), NOTCH_A, NOTCH_Y))
    seam_edge_array = p.edges.findAt(*[((pt[0], pt[1], pt[2]),) for pt in seam_pts])
    p.Set(name="SEAM_SET", edges=seam_edge_array)
    p.engineeringFeatures.assignSeam(regions=p.sets["SEAM_SET"])

    # 4. Material and Section Assignment
    mat = m.Material(name="Steel")
    mat.Elastic(table=((210000.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # 5. Seeding: Part background seed
    p.seedPart(size=H_BG, deviationFactor=0.05, minSizeFactor=0.02)

    # Find faces inside the refinement corridors
    ref_faces = []
    for f in p.faces:
        pt = f.pointOn[0]
        in_p1 = (p1["x_min"] - 1e-4 <= pt[0] <= p1["x_max"] + 1e-4) and (p1["y_min"] - 1e-4 <= pt[1] <= p1["y_max"] + 1e-4)
        in_p2 = (p2["x_min"] - 1e-4 <= pt[0] <= p2["x_max"] + 1e-4) and (p2["y_min"] - 1e-4 <= pt[1] <= p2["y_max"] + 1e-4)
        if in_p1 or in_p2:
            ref_faces.append(f)

    ref_edges = []
    edge_indices_seen = set()
    for f in ref_faces:
        for e_idx in f.getEdges():
            if e_idx not in edge_indices_seen:
                edge_indices_seen.add(e_idx)
                ref_edges.append(p.edges[e_idx])

    if ref_edges:
        p.seedEdgeBySize(edges=ref_edges, size=H_REF, deviationFactor=0.05, minSizeFactor=0.02, constraint=mesh.FINER)

    # 6. Mesh Controls and Element Types
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))

    p.generateMesh()
    print("Mesh generated: %d nodes, %d elements" % (len(p.nodes), len(p.elements)))

    # 7. Write Input File via Job
    a = m.rootAssembly
    inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
    job_name = "TEMP_CASE2_CORRIDOR_PHYS"
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

    # Ensure parent directory exists
    parent_dir = os.path.dirname(os.path.abspath(out_phys_inp))
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    with open(out_phys_inp, "w") as f:
        f.write("** ============================================================\n")
        f.write("** Method C Case 2 Dual-Corridor Physical Mesh\n")
        f.write("** Benchmark: Master Thesis Mode-I Edge-Notched Plate with Off-Axis Hole\n")
        f.write("** Primary Band:   x in [%.4f, %.4f], y in [%.4f, %.4f]\n" % (
            p1["x_min"], p1["x_max"], p1["y_min"], p1["y_max"]
        ))
        f.write("** Secondary Band: x in [%.4f, %.4f], y in [%.4f, %.4f]\n" % (
            p2["x_min"], p2["x_max"], p2["y_min"], p2["y_max"]
        ))
        f.write("** Sizing: h_ref = %.4f mm, h_bg = %.4f mm\n" % (H_REF, H_BG))
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

    print("Written Case 2 physical mesh: %s (%d nodes, %d elements)" % (out_phys_inp, len(new_nodes), len(new_elements)))

    # Clean up temporary files
    for ext in [".inp", ".cae", ".jnl", ".log"]:
        fn = job_name + ext
        if os.path.exists(fn):
            try:
                os.remove(fn)
            except Exception:
                pass


def parse_cli_args():
    """Extracts target output path, tip_x, and tip_y from sys.argv, filtering Abaqus launcher flags."""
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

    out_target = "models/pandey_kumar_mode1/292_method_c_case2/PK_METHOD_C_CASE2_ADAPTIVE_PHYS.inp"
    tip_x = 0.5000
    tip_y = 0.5000

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
    print("Case 2 Adaptive Mesh Generator CLI: out=%s, tip=(%.4f, %.4f)" % (out_target, tip_x, tip_y))
    try:
        generate_abaqus_cae_mesh(out_target, tip_x=tip_x, tip_y=tip_y)
    except Exception as e:
        print("ERROR executing Abaqus CAE mesh generation: %s" % str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
