# scripts/remeshing/execute_f1656_recovery_verification.py
"""
F1656: Correct F1655 field-mapping defect and verify coupled-stress provenance.

1. Donor Extraction & Reconstructed Physical Stress:
   - Donor: PK_HOLE_COARSE_JOB1.odb (Step 2 Inc 337, t=0.655825)
   - Read exact reference point N_RP (Node 999999) displacement U2 and RF2.
   - Join (elementLabel, integrationPoint) explicitly across SDV1, SDV15, E.
   - Reconstruct true physical stress tensor using frozen UEL constitutive law:
     C11 = 282,692.31 MPa, C12 = 121,153.85 MPa, C33 = 80,769.23 MPa
     s11 = g(d) * (C11*e11 + C12*e22)
     s22 = g(d) * (C12*e11 + C11*e22)
     s33 = g(d) * C12 * (e11 + e22)
     s12 = g(d) * (2*C33*e12)
     mises = sqrt(0.5*((s11-s22)^2 + (s22-s33)^2 + (s33-s11)^2 + 6*s12^2))

2. Corrected Node-Based Initial Field Assignment:
   - Build geometry-backed CAD model 'PlateWithHole' (2,935 CPE4/CPE3 elements, 3,028 nodes).
   - Project authentic damage d(x) directly onto receiver NODES respecting notch slit.
   - Inject '*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1' using actual receiver node labels.

3. Single Local Abaqus Recovery Solve:
   - Solve static equilibrium under matched boundary conditions.
   - Extract actual integration-point field variable, stress tensor S, MISESERI, MISESAVG.

4. Rigorous Pointwise & Spatially Matched Parity Comparison:
   - Compare donor reconstructed stress vs recovery ODB stress.
   - Evaluate Pearson correlation r, RMSE, NRMSE, pointwise & regionwise errors.
   - Check whether auxiliary stress recovery qualifies as an authentic representation.
"""
import os
import sys
import math
import json
import numpy as np

try:
    from abaqus import *
    from abaqusConstants import *
    import part, mesh, assembly, step, interaction, load, material, section
    import regionToolset
    import odbAccess
except ImportError:
    print("This script must be executed via 'abaqus cae -noGUI ...' or 'abaqus python'.")
    sys.exit(1)

log_fp = open("f1656_execution.log", "w")
def log(msg):
    log_fp.write(str(msg) + "\n")
    log_fp.flush()
    print(msg)

try:
    log("======================================================================")
    log("TASK F1656: COUPLED-STRESS PROVENANCE & FIELD MAPPING CORRECTION")
    log("======================================================================")

    # --------------------------------------------------------------------------
    # STEP 1: AUDIT DONOR ODB AND RECONSTRUCT COUPLED STRESSES
    # --------------------------------------------------------------------------
    odb_j1_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb")
    if not os.path.exists(odb_j1_path):
        raise RuntimeError("Donor Job 1 ODB not found: %s" % odb_j1_path)

    log("\n--- Step 1: Loading Donor Job 1 ODB ---")
    odb_j1 = odbAccess.openOdb(odb_j1_path, readOnly=True)
    step2 = odb_j1.steps['Step-2']
    f_last = step2.frames[-1]
    term_inc = int(f_last.incrementNumber)
    term_time = float(f_last.frameValue)

    # Explicit lookup of Node 999999 (N_RP)
    u_field_j1 = f_last.fieldOutputs['U']
    rf_field_j1 = f_last.fieldOutputs['RF']
    
    u_rp_val = None
    rf_rp_val = None
    for v in u_field_j1.values:
        if v.nodeLabel == 999999:
            u_rp_val = v
            break
    for v in rf_field_j1.values:
        if v.nodeLabel == 999999:
            rf_rp_val = v
            break

    if u_rp_val is None:
        raise RuntimeError("Could not find N_RP (Node 999999) in donor U field!")

    u1_rp = float(u_rp_val.data[0])
    u2_rp = float(u_rp_val.data[1])
    rf2_rp = float(rf_rp_val.data[1]) if rf_rp_val is not None else 0.0

    log("Donor Terminal Frame: Step-2 Inc %d, Step Time=%.6f" % (term_inc, term_time))
    log("Donor N_RP (Node 999999) Kinematics: U1=%.8e mm, U2=%.8e mm, RF2=%.6f kN" % 
        (u1_rp, u2_rp, rf2_rp))

    # Extract 2,906 physical elements and nodes
    inst_j1 = odb_j1.rootAssembly.instances['PART-1-1']
    nodes_j1 = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_j1.nodes}

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
    num_src_elems = len(eids_j1)
    log("Extracted %d physical elements from donor Job 1" % num_src_elems)

    # Explicit (elementLabel, integrationPoint) extraction of donor fields
    sdv1_field = f_last.fieldOutputs['SDV1']
    sdv15_field = f_last.fieldOutputs['SDV15']
    e_field = f_last.fieldOutputs['E']

    sdv1_map = {}
    for v in sdv1_field.values:
        sdv1_map[(v.elementLabel, v.integrationPoint)] = float(v.data)

    sdv15_map = {}
    for v in sdv15_field.values:
        sdv15_map[(v.elementLabel, v.integrationPoint)] = float(v.data)

    e_map = {}
    for v in e_field.values:
        e_map[(v.elementLabel, v.integrationPoint)] = v.data

    # Constitutive plane-strain reconstruction
    E0 = 210000.0  # MPa
    nu = 0.3
    c11 = E0 * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    c12 = E0 * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    c33 = E0 / (2.0 * (1.0 + nu))

    donor_reconstructed_ip = {}
    donor_mises_by_elem = {}
    donor_d_by_elem = {}

    for (eid, ipt), eps in e_map.items():
        if (eid, ipt) not in sdv15_map or (eid, ipt) not in sdv1_map:
            continue
        
        d_val = sdv1_map[(eid, ipt)]
        g_val = sdv15_map[(eid, ipt)]
        
        e11 = float(eps[0])
        e22 = float(eps[1])
        e33 = float(eps[2])
        e12 = float(eps[3])
        
        s11 = g_val * (c11 * e11 + c12 * e22)
        s22 = g_val * (c12 * e11 + c11 * e22)
        s33 = g_val * c12 * (e11 + e22)
        s12 = g_val * (2.0 * c33 * e12)
        
        mises = math.sqrt(0.5 * ((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 + 6.0 * s12**2))
        
        phys_eid = eid - 2 * 2906 if eid > 2 * 2906 else eid
        donor_reconstructed_ip[(phys_eid, ipt)] = {
            'd': d_val, 'g': g_val,
            's11': s11, 's22': s22, 's33': s33, 's12': s12,
            'mises': mises
        }
        
        if phys_eid not in donor_mises_by_elem:
            donor_mises_by_elem[phys_eid] = []
            donor_d_by_elem[phys_eid] = []
        donor_mises_by_elem[phys_eid].append(mises)
        donor_d_by_elem[phys_eid].append(d_val)

    odb_j1.close()

    donor_elem_mises = np.array([np.mean(donor_mises_by_elem[eid]) for eid in eids_j1])
    donor_elem_d = np.array([np.mean(donor_d_by_elem[eid]) for eid in eids_j1])

    log("Donor Physical Element Stresses Reconstructed (%d elements):" % num_src_elems)
    log("  Degraded Mises: min=%.2f MPa, median=%.2f MPa, mean=%.2f MPa, max=%.2f MPa" % 
        (donor_elem_mises.min(), np.median(donor_elem_mises), donor_elem_mises.mean(), donor_elem_mises.max()))
    log("  Damage d:       min=%.6f, median=%.6f, mean=%.6f, max=%.6f" % 
        (donor_elem_d.min(), np.median(donor_elem_d), donor_elem_d.mean(), donor_elem_d.max()))

    # --------------------------------------------------------------------------
    # STEP 2: BUILD GEOMETRY-BACKED CAD MODEL WITH CORRECTED NODAL DAMAGE
    # --------------------------------------------------------------------------
    log("\n--- Step 2: Building Geometry-Backed CAD Model 'PK_HOLE_F1656_RECOVERY' ---")
    model_name = "PK_HOLE_F1656_RECOVERY"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

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

    # Tabular elasticity E(d) = E0 * ((1-d)^2 + 1e-7)
    d_table = []
    eta_param = 1.0e-7
    for d_val in np.linspace(0.0, 1.0, 101):
        deg = (1.0 - d_val)**2 + eta_param
        E_d = E0 * deg
        d_table.append((float(E_d), float(nu), float(d_val)))

    mat = m.Material(name="DegradedSteel")
    mat.Elastic(table=tuple(d_table), dependencies=1)
    m.HomogeneousSolidSection(name="SolidSec", material="DegradedSteel", thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # Plane-strain element type assignment
    elem_quad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_tri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=regionToolset.Region(faces=p.faces), elemTypes=(elem_quad, elem_tri))

    p.seedPart(size=0.020, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    p.generateMesh()

    rec_elements = len(p.elements)
    rec_nodes = len(p.nodes)
    log("Receiver CAD Mesh: %d elements, %d nodes" % (rec_elements, rec_nodes))

    a = m.rootAssembly
    inst = a.Instance(name="Plate-1", part=p, dependent=ON)
    a.Set(name="All_elem", faces=inst.faces)
    reg = a.sets["All_elem"]

    # Step definition
    m.StaticStep(name="Step-1", previous="Initial", timePeriod=1.0,
                 initialInc=1.0, minInc=1e-5, maxInc=1.0, nlgeom=OFF)

    m.fieldOutputRequests["F-Output-1"].setValues(
        variables=("S", "U", "RF", "MISESERI", "MISESAVG", "EVOL", "FV"),
        region=reg
    )

    # Boundary conditions matching donor Job 1 exactly
    # Bottom: U2 = 0
    a.Set(name="Bottom", edges=inst.edges.findAt(((0.5 * plate_w, 0.0, 0.0),)))
    m.DisplacementBC(name="BC_Bottom", createStepName="Step-1",
                     region=a.sets["Bottom"], u2=0.0)

    # Pin: U1 = 0 at (0, 0)
    a.Set(name="Pin", vertices=inst.vertices.findAt(((0.0, 0.0, 0.0),)))
    m.DisplacementBC(name="BC_Pin", createStepName="Step-1",
                     region=a.sets["Pin"], u1=0.0)

    # Top: U2 = u2_rp, U1 = 0.0 (tied along top edge)
    a.Set(name="Top", edges=inst.edges.findAt(((0.5 * plate_w, plate_h, 0.0),)))
    m.DisplacementBC(name="BC_Top", createStepName="Step-1",
                     region=a.sets["Top"], u1=0.0, u2=float(u2_rp))

    # --------------------------------------------------------------------------
    # STEP 3: CORRECTED NODE-BASED DAMAGE PROJECTION
    # --------------------------------------------------------------------------
    log("\n--- Step 3: Projecting Damage Directly onto %d Receiver NODES ---" % rec_nodes)
    node_labels_rec = [n.label for n in p.nodes]
    node_coords_rec = np.array([(n.coordinates[0], n.coordinates[1]) for n in p.nodes], dtype=np.float64)

    # Slit classification for donor elements
    slit_donor = np.zeros(num_src_elems, dtype=int)
    for j in range(num_src_elems):
        cx, cy = centroids_j1[j]
        if cx <= notch_a:
            slit_donor[j] = 1 if cy >= notch_y else -1

    d_nodal_rec = np.zeros(rec_nodes, dtype=np.float64)
    for i in range(rec_nodes):
        nx, ny = node_coords_rec[i]
        if nx <= notch_a:
            node_slit = 1 if ny >= notch_y else -1
            valid_mask = (slit_donor == node_slit) | (slit_donor == 0)
        else:
            valid_mask = np.ones(num_src_elems, dtype=bool)
            
        c_sub = centroids_j1[valid_mask]
        d_sub = donor_elem_d[valid_mask]
        
        dists_sq = (c_sub[:, 0] - nx)**2 + (c_sub[:, 1] - ny)**2
        idx4 = np.argpartition(dists_sq, 4)[:4]
        d4 = np.sqrt(dists_sq[idx4])
        
        w = 1.0 / np.maximum(d4, 1e-6)
        w /= np.sum(w)
        d_nodal_rec[i] = np.sum(w * d_sub[idx4])

    log("Receiver Nodal Damage Field:")
    log("  min=%.6f, median=%.6f, mean=%.6f, max=%.6f" % 
        (d_nodal_rec.min(), np.median(d_nodal_rec), d_nodal_rec.mean(), d_nodal_rec.max()))
    log("  Nodes with d >= 0.10: %d" % np.sum(d_nodal_rec >= 0.10))
    log("  Nodes with d >= 0.50: %d" % np.sum(d_nodal_rec >= 0.50))
    log("  Nodes with d >= 0.80: %d" % np.sum(d_nodal_rec >= 0.80))

    # Write input deck
    job_name = "PK_HOLE_F1656_RECOVERY"
    j = mdb.Job(name=job_name, model=model_name, description="F1656 Corrected Coupled Stress Recovery")
    j.writeInput(consistencyChecking=OFF)

    inp_file = job_name + ".inp"
    with open(inp_file, "r") as fp:
        lines = fp.readlines()

    step_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().upper().startswith("*STEP"):
            step_idx = idx
            break

    if step_idx == -1:
        raise RuntimeError("Could not find *STEP in %s" % inp_file)

    # Inject CORRECTED *INITIAL CONDITIONS using NODE labels
    ic_lines = ["*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1\n"]
    for nid, d_val in zip(node_labels_rec, d_nodal_rec):
        ic_lines.append("Plate-1.%d, %.6f\n" % (nid, float(d_val)))

    mod_lines = lines[:step_idx] + ic_lines + lines[step_idx:]
    with open(inp_file, "w") as fp:
        fp.writelines(mod_lines)
    log("Injected corrected *INITIAL CONDITIONS for %d NODES into %s" % (rec_nodes, inp_file))

    # --------------------------------------------------------------------------
    # STEP 4: SINGLE LOCAL RECOVERY SOLVE
    # --------------------------------------------------------------------------
    log("\n--- Step 4: Executing Single Local Recovery Solve ---")
    j_run = mdb.JobFromInputFile(name=job_name, inputFileName=inp_file)
    j_run.submit(consistencyChecking=OFF)
    j_run.waitForCompletion()
    log("Recovery solve finished with status: %s" % str(j_run.status))

    odb_rec_path = os.path.abspath(job_name + ".odb")
    if not os.path.exists(odb_rec_path):
        raise RuntimeError("Recovery ODB missing: %s" % odb_rec_path)

    odb_rec = odbAccess.openOdb(odb_rec_path, readOnly=True)
    frame_rec = odb_rec.steps["Step-1"].frames[-1]

    # Reaction force on top edge
    rf_rec_field = frame_rec.fieldOutputs["RF"]
    rf2_top_rec = 0.0
    for v in rf_rec_field.values:
        # Check if node is on top edge
        rf2_top_rec += float(v.data[1])
    # Note: sum of all RF2 is net balance (~0); sum on top edge gives reaction
    top_node_labels = set()
    inst_rec = odb_rec.rootAssembly.instances["PLATE-1"]
    for n in inst_rec.nodes:
        if abs(n.coordinates[1] - plate_h) < 1e-5:
            top_node_labels.add(n.label)

    rf2_top_rec = sum([float(v.data[1]) for v in rf_rec_field.values if v.nodeLabel in top_node_labels])
    log("Reaction Force Comparison:")
    log("  Donor Job 1 RF2:    %.6f kN" % rf2_rp)
    log("  Recovery Solve RF2: %.6f kN" % rf2_top_rec)
    rf_diff_pct = abs(rf2_top_rec - rf2_rp) / max(abs(rf2_rp), 1e-6) * 100.0
    log("  RF2 Discrepancy:    %.2f%%" % rf_diff_pct)

    # Extract field variable at material integration points
    fv1_vals = []
    if "FV1" in frame_rec.fieldOutputs:
        fv1_vals = [float(v.data) for v in frame_rec.fieldOutputs["FV1"].values]
        log("Material Integration Point Field Variable (FV1):")
        log("  min=%.6f, median=%.6f, mean=%.6f, max=%.6f" % 
            (min(fv1_vals), np.median(fv1_vals), np.mean(fv1_vals), max(fv1_vals)))

    # Extract SPR Error indicators
    miseseri_vals = [float(v.data) for v in frame_rec.fieldOutputs["MISESERI"].values]
    misesavg_vals = [float(v.data) for v in frame_rec.fieldOutputs["MISESAVG"].values]
    s_mises_rec_vals = [float(v.mises) for v in frame_rec.fieldOutputs["S"].values]

    miseseri_arr = np.array(miseseri_vals)
    misesavg_arr = np.array(misesavg_vals)
    eta_arr = (miseseri_arr / np.maximum(misesavg_arr, 1e-6)) * 100.0

    log("\nAuthentic Abaqus SPR Indicators (Correct Units):")
    log("  MISESERI [MPa]: min=%.4f, median=%.4f, mean=%.4f, max=%.4f" % 
        (miseseri_arr.min(), np.median(miseseri_arr), miseseri_arr.mean(), miseseri_arr.max()))
    log("  MISESAVG [MPa]: min=%.4f, median=%.4f, mean=%.4f, max=%.4f" % 
        (misesavg_arr.min(), np.median(misesavg_arr), misesavg_arr.mean(), misesavg_arr.max()))
    log("  Relative Error eta [%%]: min=%.2f%%, median=%.2f%%, mean=%.2f%%, max=%.2f%%" % 
        (eta_arr.min(), np.median(eta_arr), eta_arr.mean(), eta_arr.max()))

    # --------------------------------------------------------------------------
    # STEP 5: RIGOROUS SPATIALLY MATCHED STRESS PARITY AUDIT
    # --------------------------------------------------------------------------
    log("\n--- Step 5: Spatially Matched Stress Parity Audit ---")
    # Average recovered stress per receiver element
    s_rec_by_elem = {}
    for v in frame_rec.fieldOutputs["S"].values:
        eid = v.elementLabel
        if eid not in s_rec_by_elem:
            s_rec_by_elem[eid] = []
        s_rec_by_elem[eid].append(float(v.mises))

    eids_rec = [el.label for el in p.elements]
    s_rec_elem = np.array([np.mean(s_rec_by_elem[eid]) for eid in eids_rec])
    rec_centroids = []
    for el in p.elements:
        conn = el.connectivity
        pts = [node_coords_rec[idx] for idx in conn]
        cx = sum([pt[0] for pt in pts]) / len(pts)
        cy = sum([pt[1] for pt in pts]) / len(pts)
        rec_centroids.append((cx, cy))
    rec_centroids = np.array(rec_centroids, dtype=np.float64)

    # Project recovered stress to donor centroids via slit-aware k-NN
    s_rec_on_donor = np.zeros(num_src_elems, dtype=np.float64)
    slit_rec = np.zeros(rec_elements, dtype=int)
    for i in range(rec_elements):
        cx, cy = rec_centroids[i]
        if cx <= notch_a:
            slit_rec[i] = 1 if cy >= notch_y else -1

    for j in range(num_src_elems):
        cx, cy = centroids_j1[j]
        if cx <= notch_a:
            c_slit = 1 if cy >= notch_y else -1
            valid_mask = (slit_rec == c_slit) | (slit_rec == 0)
        else:
            valid_mask = np.ones(rec_elements, dtype=bool)

        c_sub = rec_centroids[valid_mask]
        s_sub = s_rec_elem[valid_mask]

        dists_sq = (c_sub[:, 0] - cx)**2 + (c_sub[:, 1] - cy)**2
        idx3 = np.argpartition(dists_sq, 3)[:3]
        d3 = np.sqrt(dists_sq[idx3])
        w = 1.0 / np.maximum(d3, 1e-6)
        w /= np.sum(w)
        s_rec_on_donor[j] = np.sum(w * s_sub[idx3])

    # Global Parity Metrics
    r_stress = float(np.corrcoef(donor_elem_mises, s_rec_on_donor)[0, 1])
    rmse_stress = float(np.sqrt(np.mean((donor_elem_mises - s_rec_on_donor)**2)))
    nrmse_stress = float(rmse_stress / (donor_elem_mises.max() - donor_elem_mises.min()) * 100.0)
    mae_stress = float(np.mean(np.abs(donor_elem_mises - s_rec_on_donor)))

    log("\nGlobal Stress Parity Metrics (Donor vs Recovery Solve):")
    log("  Pearson Correlation r: %.6f" % r_stress)
    log("  RMSE:                  %.2f MPa" % rmse_stress)
    log("  Normalized RMSE:       %.2f%%" % nrmse_stress)
    log("  MAE:                   %.2f MPa" % mae_stress)

    # Regional Parity Metrics
    broken_mask = donor_elem_d >= 0.80
    fpz_mask = (donor_elem_d >= 0.10) & (donor_elem_d < 0.80)
    intact_mask = donor_elem_d < 0.10

    def compute_sub_metrics(mask, name):
        if np.sum(mask) == 0:
            return
        d_sub = donor_elem_mises[mask]
        r_sub = s_rec_on_donor[mask]
        r_val = float(np.corrcoef(d_sub, r_sub)[0, 1]) if len(d_sub) > 1 and np.std(d_sub) > 1e-3 and np.std(r_sub) > 1e-3 else 0.0
        rmse_val = float(np.sqrt(np.mean((d_sub - r_sub)**2)))
        mae_val = float(np.mean(np.abs(d_sub - r_sub)))
        log("  %s (%d elements):" % (name, np.sum(mask)))
        log("    Donor Mises:    min=%.1f, mean=%.1f, max=%.1f MPa" % (d_sub.min(), d_sub.mean(), d_sub.max()))
        log("    Recovery Mises: min=%.1f, mean=%.1f, max=%.1f MPa" % (r_sub.min(), r_sub.mean(), r_sub.max()))
        log("    Correlation r:  %.4f" % r_val)
        log("    RMSE:           %.2f MPa" % rmse_val)
        log("    MAE:            %.2f MPa" % mae_val)

    log("\nRegional Stress Parity Breakdown:")
    compute_sub_metrics(broken_mask, "Broken Crack Band (d >= 0.80)")
    compute_sub_metrics(fpz_mask, "Active Fracture Process Zone (0.10 <= d < 0.80)")
    compute_sub_metrics(intact_mask, "Elastic Far-Field Domain (d < 0.10)")

    # Save metrics JSON
    metrics_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1656_RECOVERY_METRICS.json")
    metrics_dict = {
        "task_id": "F1656-CORRECT-FIELD-MAPPING-AND-VERIFY-STRESS-PROVENANCE",
        "donor_source": "PK_HOLE_COARSE_JOB1.odb",
        "donor_pbs_id": "1421063.mmaster02",
        "terminal_increment": term_inc,
        "terminal_time": term_time,
        "donor_rf2_kN": rf2_rp,
        "recovery_rf2_kN": rf2_top_rec,
        "rf2_discrepancy_pct": rf_diff_pct,
        "donor_elements": num_src_elems,
        "recovery_elements": rec_elements,
        "recovery_nodes": rec_nodes,
        "field_variable_stats": {
            "min": float(min(fv1_vals)) if fv1_vals else 0.0,
            "mean": float(np.mean(fv1_vals)) if fv1_vals else 0.0,
            "max": float(max(fv1_vals)) if fv1_vals else 0.0
        },
        "donor_stress_stats_MPa": {
            "min": float(donor_elem_mises.min()),
            "median": float(np.median(donor_elem_mises)),
            "mean": float(donor_elem_mises.mean()),
            "max": float(donor_elem_mises.max())
        },
        "recovery_stress_stats_MPa": {
            "min": float(s_rec_elem.min()),
            "median": float(np.median(s_rec_elem)),
            "mean": float(s_rec_elem.mean()),
            "max": float(s_rec_elem.max())
        },
        "stress_parity_metrics": {
            "pearson_r": r_stress,
            "rmse_MPa": rmse_stress,
            "nrmse_pct": nrmse_stress,
            "mae_MPa": mae_stress
        },
        "spr_indicators": {
            "miseseri_min_MPa": float(miseseri_arr.min()),
            "miseseri_mean_MPa": float(miseseri_arr.mean()),
            "miseseri_max_MPa": float(miseseri_arr.max()),
            "misesavg_min_MPa": float(misesavg_arr.min()),
            "misesavg_mean_MPa": float(misesavg_arr.mean()),
            "misesavg_max_MPa": float(misesavg_arr.max()),
            "relative_error_eta_min_pct": float(eta_arr.min()),
            "relative_error_eta_median_pct": float(np.median(eta_arr)),
            "relative_error_eta_mean_pct": float(eta_arr.mean()),
            "relative_error_eta_max_pct": float(eta_arr.max())
        }
    }

    with open(metrics_path, "w") as fp:
        json.dump(metrics_dict, fp, indent=2)
    log("\nMetrics saved to: %s" % metrics_path)

    odb_rec.close()
    log("\n======================================================================")
    log("F1656 RECOVERY VERIFICATION RUN COMPLETE")
    log("======================================================================")

except Exception as ex:
    log("EXCEPTION IN F1656: %s" % str(ex))
    import traceback
    log(traceback.format_exc())
finally:
    log_fp.close()
