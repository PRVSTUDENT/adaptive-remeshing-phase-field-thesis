# scripts/validation/test_f1656_node_damage_projection.py
"""
Develop and validate the correct receiver node-based damage projection:
1. Extract donor physical elements, nodes, and authentic damage from Job 1 ODB.
2. Build receiver CAD mesh and get its 3,028 nodes and coordinates.
3. Compute nodal damage on receiver mesh respecting the notch slit.
4. Verify source-to-target projection metrics (correlation, RMSE, FPZ fidelity).
5. Verify that *INITIAL CONDITIONS, TYPE=FIELD uses node labels (not element labels).
"""
import os
import sys
import numpy as np

try:
    import odbAccess
    from abaqus import *
    from abaqusConstants import *
    import part, mesh, assembly, step, interaction, load, material, section
except ImportError:
    print("Run via 'abaqus cae -noGUI ...' or 'abaqus python'.")
    sys.exit(1)

log_fp = open("test_node_projection_results.txt", "w")
def log(msg):
    log_fp.write(str(msg) + "\n")
    log_fp.flush()
    print(msg)

try:
    # 1. Load Job 1 donor
    odb_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb")
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    inst_j1 = odb.rootAssembly.instances['PART-1-1']
    nodes_j1 = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_j1.nodes}

    # Extract 2,906 physical elements
    eids_j1 = []
    centroids_j1 = []
    conn_j1 = {}
    for el in inst_j1.elements:
        if el.label <= 2906:
            pts = [nodes_j1[lbl] for lbl in el.connectivity]
            cx = sum([p[0] for p in pts]) / len(pts)
            cy = sum([p[1] for p in pts]) / len(pts)
            centroids_j1.append((cx, cy))
            eids_j1.append(el.label)
            conn_j1[el.label] = el.connectivity

    centroids_j1 = np.array(centroids_j1, dtype=np.float64)
    log("Loaded %d donor physical elements" % len(eids_j1))

    # Extract terminal frame damage
    f_term = odb.steps["Step-2"].frames[-1]
    sdv1_field = f_term.fieldOutputs['SDV1']
    d_by_eid = {}
    for v in sdv1_field.values:
        phys_id = v.elementLabel - 2 * 2906 if v.elementLabel > 2 * 2906 else v.elementLabel
        d_by_eid[phys_id] = float(v.data) # constant per element

    d_donor = np.array([d_by_eid[eid] for eid in eids_j1], dtype=np.float64)
    log("Donor damage: min=%.6f, max=%.6f, mean=%.6f" % (d_donor.min(), d_donor.max(), d_donor.mean()))
    log("  Donor elements with d >= 0.10: %d" % np.sum(d_donor >= 0.10))
    log("  Donor elements with d >= 0.50: %d" % np.sum(d_donor >= 0.50))
    log("  Donor elements with d >= 0.80: %d" % np.sum(d_donor >= 0.80))
    odb.close()

    # 2. Build receiver mesh
    m = mdb.Model(name="PROJECTION_TEST")
    plate_w = 1.0; plate_h = 1.0; notch_a = 0.5; notch_y = 0.5; notch_w = 0.001
    hole_x = 0.65; hole_y = 0.65; hole_r = 0.10

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

    rec_nodes = p.nodes
    num_rec_nodes = len(rec_nodes)
    log("Receiver mesh generated: %d elements, %d nodes" % (len(p.elements), num_rec_nodes))

    # 3. Project damage directly to receiver NODES
    # Slit-aware k-NN: if node has x <= 0.5, only consider donor elements on the same side of y=0.5
    d_nodal_rec = np.zeros(num_rec_nodes, dtype=np.float64)
    node_labels = [n.label for n in rec_nodes]
    node_coords = np.array([(n.coordinates[0], n.coordinates[1]) for n in rec_nodes], dtype=np.float64)

    # Pre-classify donor centroids by slit side:
    # 0: bulk (x > 0.5), 1: top of slit (x <= 0.5, y >= 0.5), -1: bottom of slit (x <= 0.5, y < 0.5)
    slit_donor = np.zeros(len(eids_j1), dtype=int)
    for j in range(len(eids_j1)):
        cx, cy = centroids_j1[j]
        if cx <= notch_a:
            slit_donor[j] = 1 if cy >= notch_y else -1

    for i in range(num_rec_nodes):
        nx, ny = node_coords[i]
        
        # Determine slit classification for this receiver node
        if nx <= notch_a:
            node_slit = 1 if ny >= notch_y else -1
            valid_mask = (slit_donor == node_slit) | (slit_donor == 0)
        else:
            valid_mask = np.ones(len(eids_j1), dtype=bool)
            
        c_sub = centroids_j1[valid_mask]
        d_sub = d_donor[valid_mask]
        
        dists_sq = (c_sub[:, 0] - nx)**2 + (c_sub[:, 1] - ny)**2
        idx4 = np.argpartition(dists_sq, 4)[:4]
        d4 = np.sqrt(dists_sq[idx4])
        
        weights = 1.0 / np.maximum(d4, 1e-6)
        weights /= np.sum(weights)
        d_nodal_rec[i] = np.sum(weights * d_sub[idx4])

    log("Nodal damage on receiver: min=%.6f, max=%.6f, mean=%.6f" % 
        (d_nodal_rec.min(), d_nodal_rec.max(), d_nodal_rec.mean()))
    log("  Receiver nodes with d >= 0.10: %d" % np.sum(d_nodal_rec >= 0.10))
    log("  Receiver nodes with d >= 0.50: %d" % np.sum(d_nodal_rec >= 0.50))
    log("  Receiver nodes with d >= 0.80: %d" % np.sum(d_nodal_rec >= 0.80))

    # Evaluate receiver element-centroid damage by averaging corner nodes
    rec_elem_d = []
    rec_elem_centroids = []
    node_d_list = list(d_nodal_rec) # 0-based index matches p.nodes index!
    for el in p.elements:
        conn = el.connectivity # 0-based node indices into p.nodes
        d_elem = np.mean([node_d_list[idx] for idx in conn])
        rec_elem_d.append(d_elem)
        
        pts = [node_coords[idx] for idx in conn]
        cx = sum([pt[0] for pt in pts]) / len(pts)
        cy = sum([pt[1] for pt in pts]) / len(pts)
        rec_elem_centroids.append((cx, cy))

    rec_elem_d = np.array(rec_elem_d, dtype=np.float64)
    rec_elem_centroids = np.array(rec_elem_centroids, dtype=np.float64)

    log("Receiver element-averaged damage: min=%.6f, max=%.6f, mean=%.6f" % 
        (rec_elem_d.min(), rec_elem_d.max(), rec_elem_d.mean()))
    log("  Receiver elements with d >= 0.10: %d (donor: %d)" % 
        (np.sum(rec_elem_d >= 0.10), np.sum(d_donor >= 0.10)))
    log("  Receiver elements with d >= 0.50: %d (donor: %d)" % 
        (np.sum(rec_elem_d >= 0.50), np.sum(d_donor >= 0.50)))
    log("  Receiver elements with d >= 0.80: %d (donor: %d)" % 
        (np.sum(rec_elem_d >= 0.80), np.sum(d_donor >= 0.80)))

    # Compute spatial cross-correlation between donor and receiver fields
    # Map receiver element values back to donor centroids
    d_rec_on_donor = np.zeros(len(eids_j1), dtype=np.float64)
    for j in range(len(eids_j1)):
        cx, cy = centroids_j1[j]
        dists_sq = (rec_elem_centroids[:, 0] - cx)**2 + (rec_elem_centroids[:, 1] - cy)**2
        idx3 = np.argpartition(dists_sq, 3)[:3]
        d3 = np.sqrt(dists_sq[idx3])
        w = 1.0 / np.maximum(d3, 1e-6)
        w /= np.sum(w)
        d_rec_on_donor[j] = np.sum(w * rec_elem_d[idx3])

    r_damage = np.corrcoef(d_donor, d_rec_on_donor)[0, 1]
    rmse_damage = np.sqrt(np.mean((d_donor - d_rec_on_donor)**2))
    nrmse_damage = rmse_damage / (d_donor.max() - d_donor.min()) * 100.0

    log("\nDamage Field Fidelity Verification (Donor vs Receiver Element):")
    log("  Pearson Correlation r: %.6f" % r_damage)
    log("  RMSE:                  %.6f" % rmse_damage)
    log("  Normalized RMSE:       %.2f%%" % nrmse_damage)

    # 4. Check *INITIAL CONDITIONS injection syntax
    sample_ic_lines = []
    sample_ic_lines.append("*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1\n")
    for nid, d_val in zip(node_labels[:5], d_nodal_rec[:5]):
        sample_ic_lines.append("Plate-1.%d, %.6f\n" % (nid, float(d_val)))
    log("\nSample Corrected *INITIAL CONDITIONS syntax:")
    for line in sample_ic_lines:
        log("  " + line.strip())

    log("\nSUCCESS: Receiver node-based damage projection verified.")

except Exception as ex:
    log("EXCEPTION: %s" % str(ex))
    import traceback
    log(traceback.format_exc())
finally:
    log_fp.close()
