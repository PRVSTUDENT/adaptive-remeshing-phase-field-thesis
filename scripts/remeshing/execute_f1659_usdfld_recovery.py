# scripts/remeshing/execute_f1659_usdfld_recovery.py
"""
Task F1659: One Gated USDFLD Recovery Pilot

Implements the exact directive from ChatGPT Independent Scientific Review:
1. Builds geometry-backed CAD model (PlateWithHole, 2,935 elements).
2. Generates clustered field-dependent elastic table (371 points, max error < 0.23%, error at peak < 0.03%).
3. Attaches auxiliary USDFLD user subroutine (f1659_recovery_usdfld.for) with direct IP lookup.
4. Solves static equilibrium with donor boundary kinematics (u2 = 0.00959078 mm).
5. Extracts:
   - Integration-point FV1: checks damage preservation (target d_max = 0.9976)
   - Reaction force RF2: evaluates parity with donor (0.216354 kN)
   - Degraded physical Mises stress: evaluates global & regime-specific Pearson r and RMSE
   - Abaqus SPR error indicator MISESERI & MISESAVG
6. Exports PK_HOLE_F1659_RECOVERY_METRICS.json.
"""
import os
import sys
import math
import json
import shutil
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

log_fp = open("f1659_execution.log", "w")
def log(msg):
    log_fp.write(str(msg) + "\n")
    log_fp.flush()
    print(msg)

try:
    log("======================================================================")
    log("TASK F1659: GATED USDFLD AUXILIARY STRESS RECOVERY PILOT")
    log("======================================================================")

    # --------------------------------------------------------------------------
    # 1. VERIFY PRECONDITIONS & LOOKUP TABLE
    # --------------------------------------------------------------------------
    lookup_src = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1659_IP_DAMAGE_LOOKUP.txt")
    usdfld_src = os.path.abspath("scripts/remeshing/f1659_recovery_usdfld.for")
    donor_odb_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb")

    if not os.path.exists(lookup_src):
        raise RuntimeError("Lookup table not found: %s" % lookup_src)
    if not os.path.exists(usdfld_src):
        raise RuntimeError("USDFLD Fortran file not found: %s" % usdfld_src)
    if not os.path.exists(donor_odb_path):
        raise RuntimeError("Donor ODB not found: %s" % donor_odb_path)

    # Copy lookup table to current working directory so USDFLD finds it
    shutil.copy(lookup_src, "PK_HOLE_F1659_IP_DAMAGE_LOOKUP.txt")
    log("Verified and staged lookup table: PK_HOLE_F1659_IP_DAMAGE_LOOKUP.txt")

    # --------------------------------------------------------------------------
    # 2. AUDIT DONOR ODB & EXTRACT REFERENCE VALUES
    # --------------------------------------------------------------------------
    log("\n--- 2. Loading Donor Job 1 Reference Values ---")
    odb_j1 = odbAccess.openOdb(donor_odb_path, readOnly=True)
    f_last = odb_j1.steps['Step-2'].frames[-1]

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

    u2_donor = float(u_rp_val.data[1])
    rf2_donor = float(rf_rp_val.data[1])
    log("Donor Terminal Displacement: u2 = %.8f mm" % u2_donor)
    log("Donor Terminal Reaction Force: RF2 = %.6f kN" % rf2_donor)

    # Reconstruct donor stresses for parity comparison
    sdv1_field = f_last.fieldOutputs['SDV1']
    sdv15_field = f_last.fieldOutputs['SDV15']
    e_field = f_last.fieldOutputs['E']

    sdv1_map = {(v.elementLabel, v.integrationPoint): float(v.data) for v in sdv1_field.values}
    sdv15_map = {(v.elementLabel, v.integrationPoint): float(v.data) for v in sdv15_field.values}
    e_map = {(v.elementLabel, v.integrationPoint): v.data for v in e_field.values}

    E0 = 210000.0  # MPa
    nu = 0.3
    c11 = E0 * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    c12 = E0 * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    c33 = E0 / (2.0 * (1.0 + nu))

    donor_mises_by_elem = {}
    donor_d_by_elem = {}
    for (eid, ipt), eps in e_map.items():
        if (eid, ipt) not in sdv15_map or (eid, ipt) not in sdv1_map:
            continue
        d_val = sdv1_map[(eid, ipt)]
        g_val = sdv15_map[(eid, ipt)]
        e11, e22, e33_val, e12 = float(eps[0]), float(eps[1]), float(eps[2]), float(eps[3])
        s11 = g_val * (c11 * e11 + c12 * e22)
        s22 = g_val * (c12 * e11 + c11 * e22)
        s33_s = g_val * c12 * (e11 + e22)
        s12_s = g_val * (2.0 * c33 * e12)
        mises = math.sqrt(0.5 * ((s11 - s22)**2 + (s22 - s33_s)**2 + (s33_s - s11)**2 + 6.0 * s12_s**2))
        
        phys_eid = eid - 2 * 2906 if eid > 2 * 2906 else eid
        donor_mises_by_elem.setdefault(phys_eid, []).append(mises)
        donor_d_by_elem.setdefault(phys_eid, []).append(d_val)

    odb_j1.close()

    # --------------------------------------------------------------------------
    # 3. BUILD GEOMETRY-BACKED CAD MODEL WITH USDFLD MATERIAL
    # --------------------------------------------------------------------------
    log("\n--- 3. Building Geometry-Backed CAD Model 'PK_HOLE_F1659_RECOVERY' ---")
    model_name = "PK_HOLE_F1659_RECOVERY"
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

    # Build clustered elasticity table (371 points, max error < 0.23%)
    d1 = np.linspace(0.0, 0.90, 91)
    d2 = np.linspace(0.901, 0.990, 90)
    d3 = np.linspace(0.9901, 0.9990, 90)
    d4 = np.linspace(0.99901, 1.0000, 100)
    d_grid = np.unique(np.concatenate([d1, d2, d3, d4]))
    k_res = 1.0e-7

    elastic_table = []
    for d_val in d_grid:
        deg = (1.0 - d_val)**2 + k_res
        E_eff = float(E0 * deg)
        elastic_table.append((E_eff, 0.3, float(d_val)))

    mat = m.Material(name="DamagedElastic_USDFLD")
    mat.UserDefinedField()
    mat.Elastic(table=tuple(elastic_table), dependencies=1)

    m.HomogeneousSolidSection(name="PlateSection", material="DamagedElastic_USDFLD", thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="PlateSection")

    # Generate Mesh
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
    a.Set(name="Bottom", edges=inst.edges.findAt(((0.5 * plate_w, 0.0, 0.0),)))
    m.DisplacementBC(name="BC_Bottom", createStepName="Step-1",
                     region=a.sets["Bottom"], u2=0.0)

    a.Set(name="Pin", vertices=inst.vertices.findAt(((0.0, 0.0, 0.0),)))
    m.DisplacementBC(name="BC_Pin", createStepName="Step-1",
                     region=a.sets["Pin"], u1=0.0)

    a.Set(name="Top", edges=inst.edges.findAt(((0.5 * plate_w, plate_h, 0.0),)))
    m.DisplacementBC(name="BC_Top", createStepName="Step-1",
                     region=a.sets["Top"], u1=0.0, u2=float(u2_donor))

    # Write input deck
    job_name = "PK_HOLE_F1659_RECOVERY"
    log("\n--- 4. Writing Input Deck '%s.inp' ---" % job_name)
    m_job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS,
                    userSubroutine=usdfld_src)
    m_job.writeInput(consistencyChecking=OFF)
    inp_path = os.path.abspath(job_name + ".inp")
    log("Input deck written: %s (%d bytes)" % (inp_path, os.path.getsize(inp_path)))

    # --------------------------------------------------------------------------
    # 5. EXECUTE LOCAL ABAQUS/STANDARD SOLVE WITH USDFLD
    # --------------------------------------------------------------------------
    log("\n--- 5. Executing Local Abaqus/Standard Solve with USDFLD ---")
    log("Compiling and running: abaqus job=%s user=%s interactive" % (job_name, usdfld_src))
    
    # Run via bat script calling vcvars64 + setvars to ensure compiler is active
    bat_content = (
        "@echo off\n"
        "call \"C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat\"\n"
        "call \"C:\\Program Files (x86)\\Intel\\oneAPI\\setvars.bat\" intel64 vs2022\n"
        "abaqus job=%s user=\"%s\" interactive\n" % (job_name, usdfld_src)
    )
    with open("run_f1659_solve.bat", "w") as fp:
        fp.write(bat_content)
    
    ret = os.system("run_f1659_solve.bat")
    if ret != 0:
        raise RuntimeError("Abaqus solve failed with return code: %d" % ret)

    log("Abaqus solve finished successfully (Exit 0)")

    # --------------------------------------------------------------------------
    # 6. EXTRACT RESULTS & AUDIT PARITY
    # --------------------------------------------------------------------------
    rec_odb_path = os.path.abspath(job_name + ".odb")
    if not os.path.exists(rec_odb_path):
        raise RuntimeError("Recovery ODB not found: %s" % rec_odb_path)

    log("\n--- 6. Extracting Results from Recovery ODB ---")
    odb_rec = odbAccess.openOdb(rec_odb_path, readOnly=True)
    inst_rec = odb_rec.rootAssembly.instances['PLATE-1']
    f_rec = odb_rec.steps['Step-1'].frames[-1]

    # Reaction force extraction
    rf_field_rec = f_rec.fieldOutputs['RF']
    top_node_labels = set([n.label for n in inst_rec.nodes if abs(n.coordinates[1] - 1.0) < 1e-4])
    rf2_tot_N = sum([float(v.data[1]) for v in rf_field_rec.values if v.nodeLabel in top_node_labels])
    rf2_rec_kN = rf2_tot_N / 1000.0  # E was in MPa = N/mm^2, so RF is in N -> divide by 1000 to get kN

    log("Reaction Force Audit:")
    log("  Donor Job 1 RF2:    %.6f kN" % rf2_donor)
    log("  F1659 Recovery RF2: %.6f kN" % rf2_rec_kN)
    log("  Discrepancy:        %+.2f%% (Ratio: %.2fx)" % 
        (((rf2_rec_kN - rf2_donor) / rf2_donor) * 100.0, rf2_rec_kN / rf2_donor))

    # Field variable FV1 audit
    fv1_field = f_rec.fieldOutputs['FV1']
    fv1_vals = [float(v.data) for v in fv1_field.values]
    fv1_min = min(fv1_vals)
    fv1_mean = float(np.mean(fv1_vals))
    fv1_max = max(fv1_vals)

    log("\nIntegration-Point Damage (FV1) Audit:")
    log("  FV1 min:    %.6f" % fv1_min)
    log("  FV1 mean:   %.6f" % fv1_mean)
    log("  FV1 max:    %.6f (Target Donor d_max: 0.997577)" % fv1_max)
    log("  IPs with FV1 >= 0.80: %d" % sum(1 for v in fv1_vals if v >= 0.80))
    log("  IPs with FV1 >= 0.90: %d" % sum(1 for v in fv1_vals if v >= 0.90))
    log("  IPs with FV1 >= 0.99: %d" % sum(1 for v in fv1_vals if v >= 0.99))

    # Degraded physical stress & MISESERI extraction
    s_field = f_rec.fieldOutputs['S']
    miseseri_field = f_rec.fieldOutputs['MISESERI']
    misesavg_field = f_rec.fieldOutputs['MISESAVG']

    rec_mises_by_elem = {}
    for v in s_field.values:
        rec_mises_by_elem.setdefault(v.elementLabel, []).append(float(v.mises))

    rec_elem_mises = np.array([np.mean(rec_mises_by_elem[eid]) for eid in sorted(rec_mises_by_elem.keys())])
    
    miseseri_vals = np.array([float(v.data) for v in miseseri_field.values])
    misesavg_vals = np.array([float(v.data) for v in misesavg_field.values])
    eta_vals = (miseseri_vals / np.maximum(misesavg_vals, 1e-6)) * 100.0

    log("\nStress & Error Indicator Statistics:")
    log("  Recovery Mises:   min=%.2f MPa, median=%.2f MPa, mean=%.2f MPa, max=%.2f MPa" % 
        (rec_elem_mises.min(), np.median(rec_elem_mises), rec_elem_mises.mean(), rec_elem_mises.max()))
    log("  MISESERI [MPa]:   min=%.4f, median=%.4f, mean=%.4f, max=%.4f" % 
        (miseseri_vals.min(), np.median(miseseri_vals), miseseri_vals.mean(), miseseri_vals.max()))
    log("  Relative Error eta: min=%.2f%%, median=%.2f%%, mean=%.2f%%, max=%.2f%%" % 
        (eta_vals.min(), np.median(eta_vals), eta_vals.mean(), eta_vals.max()))

    # Spatial stress correlation with donor
    # Spatially match receiver elements to nearest donor elements
    rec_centroids = []
    for eid in sorted(rec_mises_by_elem.keys()):
        conn = p.elements[eid - 1].connectivity
        pts = [p.nodes[lbl].coordinates for lbl in conn]
        rec_centroids.append((sum(pt[0] for pt in pts)/len(pts), sum(pt[1] for pt in pts)/len(pts)))
    rec_centroids = np.array(rec_centroids)

    donor_centroids = []
    donor_mises_list = []
    donor_d_list = []
    for eid in sorted(donor_mises_by_elem.keys()):
        pts = [donor_nodes[lbl] for lbl in donor_elems[eid]]
        donor_centroids.append((sum(pt[0] for pt in pts)/len(pts), sum(pt[1] for pt in pts)/len(pts)))
        donor_mises_list.append(np.mean(donor_mises_by_elem[eid]))
        donor_d_list.append(np.mean(donor_d_by_elem[eid]))
    donor_centroids = np.array(donor_centroids)
    donor_mises_arr = np.array(donor_mises_list)
    donor_d_arr = np.array(donor_d_list)

    # Nearest neighbor join
    matched_donor_mises = []
    matched_donor_d = []
    for rc in rec_centroids:
        dists_sq = (donor_centroids[:, 0] - rc[0])**2 + (donor_centroids[:, 1] - rc[1])**2
        min_idx = np.argmin(dists_sq)
        matched_donor_mises.append(donor_mises_arr[min_idx])
        matched_donor_d.append(donor_d_arr[min_idx])
    matched_donor_mises = np.array(matched_donor_mises)
    matched_donor_d = np.array(matched_donor_d)

    # Correlation metrics
    r_global = float(np.corrcoef(matched_donor_mises, rec_elem_mises)[0, 1])
    diff = rec_elem_mises - matched_donor_mises
    rmse_global = float(np.sqrt(np.mean(diff**2)))
    nrmse_global = float((rmse_global / (matched_donor_mises.max() - matched_donor_mises.min())) * 100.0)

    # Far-field correlation (d < 0.10)
    far_mask = matched_donor_d < 0.10
    r_far = float(np.corrcoef(matched_donor_mises[far_mask], rec_elem_mises[far_mask])[0, 1])
    rmse_far = float(np.sqrt(np.mean(diff[far_mask]**2)))

    # Softened band (0.10 <= d < 0.80)
    soft_mask = (matched_donor_d >= 0.10) & (matched_donor_d < 0.80)
    r_soft = float(np.corrcoef(matched_donor_mises[soft_mask], rec_elem_mises[soft_mask])[0, 1]) if np.sum(soft_mask) > 5 else 0.0
    rmse_soft = float(np.sqrt(np.mean(diff[soft_mask]**2))) if np.sum(soft_mask) > 5 else 0.0

    # Broken crack band (d >= 0.80)
    broken_mask = matched_donor_d >= 0.80
    r_broken = float(np.corrcoef(matched_donor_mises[broken_mask], rec_elem_mises[broken_mask])[0, 1]) if np.sum(broken_mask) > 5 else 0.0
    rmse_broken = float(np.sqrt(np.mean(diff[broken_mask]**2))) if np.sum(broken_mask) > 5 else 0.0
    broken_mean_rec = float(np.mean(rec_elem_mises[broken_mask])) if np.sum(broken_mask) > 0 else 0.0
    broken_mean_donor = float(np.mean(matched_donor_mises[broken_mask])) if np.sum(broken_mask) > 0 else 0.0

    log("\nStress Parity Comparison:")
    log("  Global Pearson r:       %.4f" % r_global)
    log("  Global RMSE:            %.2f MPa (NRMSE: %.2f%%)" % (rmse_global, nrmse_global))
    log("  Far-Field r (d < 0.10): %.4f (RMSE: %.2f MPa, %d elements)" % 
        (r_far, rmse_far, np.sum(far_mask)))
    log("  Softened r (0.10<=d<0.80): %.4f (RMSE: %.2f MPa, %d elements)" % 
        (r_soft, rmse_soft, np.sum(soft_mask)))
    log("  Broken Band r (d >= 0.80): %.4f (RMSE: %.2f MPa, %d elements)" % 
        (r_broken, rmse_broken, np.sum(broken_mask)))
    log("  Broken Band Mean Mises: Recovery = %.1f MPa vs Donor = %.1f MPa" % 
        (broken_mean_rec, broken_mean_donor))

    odb_rec.close()

    # Save metrics JSON
    metrics = {
        "task_id": "F1659-GATED-USDFLD-RECOVERY-PILOT",
        "solver_exit_code": 0,
        "donor_rf2_kN": float(rf2_donor),
        "recovery_rf2_kN": float(rf2_rec_kN),
        "rf2_discrepancy_pct": float(((rf2_rec_kN - rf2_donor) / rf2_donor) * 100.0),
        "rf2_ratio": float(rf2_rec_kN / rf2_donor),
        "fv1_min": float(fv1_min),
        "fv1_mean": float(fv1_mean),
        "fv1_max": float(fv1_max),
        "fv1_target_parity": float(fv1_max / 0.9975769519805908),
        "ip_counts": {
            "fv1_ge_080": int(sum(1 for v in fv1_vals if v >= 0.80)),
            "fv1_ge_090": int(sum(1 for v in fv1_vals if v >= 0.90)),
            "fv1_ge_095": int(sum(1 for v in fv1_vals if v >= 0.95)),
            "fv1_ge_099": int(sum(1 for v in fv1_vals if v >= 0.99))
        },
        "stress_parity": {
            "r_global": float(r_global),
            "rmse_global_MPa": float(rmse_global),
            "nrmse_global_pct": float(nrmse_global),
            "r_far_field": float(r_far),
            "rmse_far_field_MPa": float(rmse_far),
            "r_softened": float(r_soft),
            "rmse_softened_MPa": float(rmse_soft),
            "r_broken_band": float(r_broken),
            "rmse_broken_band_MPa": float(rmse_broken),
            "broken_band_mean_recovery_MPa": float(broken_mean_rec),
            "broken_band_mean_donor_MPa": float(broken_mean_donor)
        },
        "miseseri_stats": {
            "min_MPa": float(miseseri_vals.min()),
            "median_MPa": float(np.median(miseseri_vals)),
            "mean_MPa": float(miseseri_vals.mean()),
            "max_MPa": float(miseseri_vals.max()),
            "relative_error_median_pct": float(np.median(eta_vals)),
            "relative_error_mean_pct": float(eta_vals.mean()),
            "relative_error_max_pct": float(eta_vals.max())
        }
    }

    metrics_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1659_RECOVERY_METRICS.json")
    with open(metrics_path, "w") as fp:
        json.dump(metrics, fp, indent=2)
    log("\nMetrics saved to: %s" % metrics_path)

    # Save plot data for figures
    plot_data = {
        "rec_centroids": rec_centroids.tolist(),
        "rec_elem_mises": rec_elem_mises.tolist(),
        "matched_donor_mises": matched_donor_mises.tolist(),
        "matched_donor_d": matched_donor_d.tolist(),
        "diff_mises": diff.tolist(),
        "fv1_vals": fv1_vals,
        "miseseri_vals": miseseri_vals.tolist(),
        "donor_rf2": float(rf2_donor),
        "rec_rf2": float(rf2_rec_kN)
    }
    with open("f1659_plot_data.json", "w") as fp:
        json.dump(plot_data, fp)
    log("Plot data saved to: f1659_plot_data.json")

    log("\n======================================================================")
    log("F1659 USDFLD RECOVERY PILOT COMPLETE")
    log("======================================================================")

except Exception as ex:
    log("EXCEPTION IN F1659: %s" % str(ex))
    import traceback
    log(traceback.format_exc())
finally:
    log_fp.close()
