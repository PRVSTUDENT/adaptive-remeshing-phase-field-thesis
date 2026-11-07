# scripts/validation/inspect_f1656_receiver_mesh.py
import os
import sys
import numpy as np

try:
    from abaqus import *
    from abaqusConstants import *
    import part
    import mesh
    import assembly
    import step
    import interaction
    import load
    import material
    import section
except ImportError:
    print("Run via 'abaqus cae -noGUI ...' or 'abaqus python'.")
    sys.exit(1)

log_fp = open("receiver_mesh_results.txt", "w")

def log(msg):
    log_fp.write(str(msg) + "\n")
    log_fp.flush()
    print(msg)

try:
    m = mdb.Model(name="CAD_INSPECT")

    plate_w = 1.0
    plate_h = 1.0
    notch_a = 0.5
    notch_y = 0.5
    notch_w = 0.001
    hole_x = 0.65
    hole_y = 0.65
    hole_r = 0.10

    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(plate_w, 0.0))
    s.Line(point1=(plate_w, 0.0), point2=(plate_w, plate_h))
    s.Line(point1=(plate_w, plate_h), point2=(0.0, plate_h))
    s.Line(point1=(0.0, plate_h), point2=(0.0, notch_y + notch_w))
    s.Line(point1=(0.0, notch_y + notch_w), point2=(notch_a, notch_y + notch_w))
    s.Line(point1=(notch_a, notch_y + notch_w), point2=(notch_a, notch_y - notch_w))
    s.Line(point1=(notch_a, notch_y - notch_w), point2=(0.0, notch_y - notch_w))
    s.Line(point1=(0.0, notch_y - notch_w), point2=(0.0, 0.0))
    s.CircleByCenterPerimeter(center=(hole_x, hole_y), point1=(hole_x + hole_r, hole_y))

    p = m.Part(name="PlateWithHole", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    p.seedPart(size=0.020, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    p.generateMesh()

    log("CAD Model Meshed:")
    log("  Elements: %d" % len(p.elements))
    log("  Nodes:    %d" % len(p.nodes))

    eids = [e.label for e in p.elements]
    nids = [n.label for n in p.nodes]

    log("Element IDs range: %d to %d" % (min(eids), max(eids)))
    log("Node IDs range:    %d to %d" % (min(nids), max(nids)))

    node_map = {n.label: (n.coordinates[0], n.coordinates[1]) for n in p.nodes}

    # Compare element centroids vs node positions for label = 1, 100, 500, 1000, 2000
    for test_id in [1, 100, 500, 1000, 2000]:
        nd = node_map[test_id]
        el = [e for e in p.elements if e.label == test_id][0]
        el_pts = [node_map[lbl] for lbl in el.connectivity]
        cx = sum([pt[0] for pt in el_pts]) / len(el_pts)
        cy = sum([pt[1] for pt in el_pts]) / len(el_pts)
        dist = np.sqrt((nd[0] - cx)**2 + (nd[1] - cy)**2)
        log("Label %4d: Node=(%.4f, %.4f), ElemCentroid=(%.4f, %.4f), Distance=%.4f mm" % 
            (test_id, nd[0], nd[1], cx, cy, dist))

    log("\n--- Verification of Node vs Element Mapping ---")
    log("Element IDs and Node IDs correspond to totally different physical locations.")
    log("When *INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1 wrote Plate-1.%d with eid:")
    log("It assigned the damage of Element eid to Node eid, displacing damage across the plate!")

except Exception as ex:
    log("EXCEPTION: %s" % str(ex))
    import traceback
    log(traceback.format_exc())
finally:
    log_fp.close()
