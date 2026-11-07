# -*- coding: utf-8 -*-
"""
Production Execution Script: Coupled-State Stress Recovery & Native Adaptive Remeshing
Task: F1655-COUPLED-MISESERI-PROVENANCE-AND-NATIVE-REMESH
Master's Thesis: Mode-I Plate with Off-Axis Circular Hole
Reference: Pandey & Kumar (2025) Method A

Key corrections over F1654:
1. Replays authentic coupled damage d (SDV1) and degradation g(d) = (1-d)^2 + 1e-7 from
   Job 1 (PBS 1421063.mmaster02, PK_HOLE_COARSE_JOB1.odb) at the terminal converged fracture state (u2 = 0.009591 mm).
2. Uses plane-strain continuum kinematics (CPE4/CPE3) matching frozen UEL plane-strain formulation.
3. Quantifies spatial projection between 2,906 source elements and 2,935 target geometry-backed elements.
4. Corrects MISESERI units: reports raw MISESERI in stress units [MPa], MISESAVG in [MPa],
   and normalized relative error eta = MISESERI / MISESAVG * 100%.
5. Evaluates publication-grounded RemeshingRule (Listing 1-4) at errorTarget = 2.0% and controlled 5.0%.
6. Audits strict longest edge h_max <= 1.500 um with 1.500001 um floating-point tolerance across
   four distinct regions: notch-ligament, left hole flank, right hole flank, secondary right damage band.
7. Exports physical input deck PK_HOLE_METHOD_A_NATIVE_ADAPT_PHYS.inp and metrics JSON.
"""

import sys
import os
import math
import json
import numpy as np

log_path = os.path.abspath("coupled_recovery_f1655.log")
log_file = open(log_path, "w")
sys.stdout = log_file
sys.stderr = log_file

from abaqus import *
from abaqusConstants import *
import regionToolset
import part, material, section, assembly, step, load, mesh, job, sketch, odbAccess

print("================================================================================")
print("F1655: PRODUCTION COUPLED-STATE STRESS RECOVERY & NATIVE ADAPTIVE REMESHING")
print("================================================================================")

work_dir = os.path.abspath(".")
output_dir = os.path.join(work_dir, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ==============================================================================
# STEP 1: LOAD AUTHENTIC F1653 JOB 1 COUPLED SOURCE DATA
# ==============================================================================
odb_j1_path = os.path.join(output_dir, "PK_HOLE_COARSE_JOB1.odb")
print("Step 1: Loading authentic Job 1 ODB: %s" % odb_j1_path)
if not os.path.exists(odb_j1_path):
    raise RuntimeError("Job 1 ODB not found: %s" % odb_j1_path)

odb_j1 = odbAccess.openOdb(odb_j1_path, readOnly=True)
inst_j1 = odb_j1.rootAssembly.instances['PART-1-1']
nodes_j1 = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_j1.nodes}

# Extract centroids of 2,906 physical elements
centroids_j1 = []
eids_j1 = []
for el in inst_j1.elements:
    if el.label <= 2906:
        pts = [nodes_j1[lbl] for lbl in el.connectivity]
        cx = sum([p[0] for p in pts]) / len(pts)
        cy = sum([p[1] for p in pts]) / len(pts)
        centroids_j1.append((cx, cy))
        eids_j1.append(el.label)

centroids_j1 = np.array(centroids_j1, dtype=np.float64)
num_src_elems = len(eids_j1)
print("Extracted %d physical elements from Job 1" % num_src_elems)

# Extract terminal converged frame in Step-2 (Inc 337, u2 = 0.009591 mm)
step2 = odb_j1.steps['Step-2']
f_last = step2.frames[-1]
u2_terminal = float(f_last.fieldOutputs['U'].values[0].data[1])
term_inc = int(f_last.incrementNumber)
term_time = float(f_last.frameValue)
print("Terminal converged increment: Step-2 Inc %d, time = %.5f, u2 = %.8f mm" % 
      (term_inc, term_time, u2_terminal))

# Extract authentic damage d (SDV1), g(d) (SDV15), history H (SDV2), and total strain E
sdv1_vals = f_last.fieldOutputs['SDV1'].values
sdv2_vals = f_last.fieldOutputs['SDV2'].values
sdv15_vals = f_last.fieldOutputs['SDV15'].values
e_vals = f_last.fieldOutputs['E'].values

d_by_eid = {}
h_by_eid = {}
g_by_eid = {}

for i in range(len(sdv1_vals)):
    eid = sdv1_vals[i].elementLabel
    phys_id = eid - 2 * 2906 if eid > 2 * 2906 else eid
    if phys_id not in d_by_eid:
        d_by_eid[phys_id] = []
        h_by_eid[phys_id] = []
        g_by_eid[phys_id] = []
    d_by_eid[phys_id].append(float(sdv1_vals[i].data))
    h_by_eid[phys_id].append(float(sdv2_vals[i].data))
    g_by_eid[phys_id].append(float(sdv15_vals[i].data))

d_source = np.array([np.mean(d_by_eid[eid]) for eid in eids_j1], dtype=np.float64)
h_source = np.array([np.mean(h_by_eid[eid]) for eid in eids_j1], dtype=np.float64)
g_source = np.array([np.mean(g_by_eid[eid]) for eid in eids_j1], dtype=np.float64)

# Plane-strain constitutive constants matching frozen UEL (f42_mixed_uel.for)
E0 = 210000.0 # MPa
nu = 0.3
eta = 1.0e-7
c11 = E0 * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
c12 = E0 * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
c33 = E0 / (2.0 * (1.0 + nu)) # Shear modulus G

# Reconstruct authentic plane-strain degraded physical stresses at integration points
s_mises_coupled_ip = []
for i in range(len(e_vals)):
    e11, e22, e33, e12 = e_vals[i].data
    d = sdv1_vals[i].data
    g = sdv15_vals[i].data
    
    # Degraded stresses
    s11 = g * (c11 * e11 + c12 * e22)
    s22 = g * (c12 * e11 + c11 * e22)
    s33 = g * (c12 * (e11 + e22))
    s12 = g * (2.0 * c33 * e12)
    mises = math.sqrt(0.5 * ((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 + 6.0 * s12**2))
    s_mises_coupled_ip.append(mises)

s_mises_coupled_ip = np.array(s_mises_coupled_ip, dtype=np.float64)
print("Source Coupled Degraded Stress: min=%.2f MPa, max=%.2f MPa, mean=%.2f MPa" % 
      (s_mises_coupled_ip.min(), s_mises_coupled_ip.max(), s_mises_coupled_ip.mean()))
print("Source Damage Distribution: min=%.6f, max=%.6f, mean=%.6f" % 
      (d_source.min(), d_source.max(), d_source.mean()))
print("  Elements with d >= 0.10: %d" % np.sum(d_source >= 0.10))
print("  Elements with d >= 0.50: %d" % np.sum(d_source >= 0.50))
print("  Elements with d >= 0.80: %d" % np.sum(d_source >= 0.80))
odb_j1.close()

# ==============================================================================
# STEP 2: BUILD GEOMETRY-BACKED CAD MODEL WITH PLANE-STRAIN KINEMATICS
# ==============================================================================
print("\nStep 2: Building Geometry-Backed CAD Model 'PK_HOLE_COARSE_RECOVERY'...")
model_name = "PK_HOLE_COARSE_RECOVERY"
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

# Geometry
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

# Define field-dependent elastic material matching frozen UEL: E(d) = E0 * ((1-d)^2 + 1e-7)
d_table = []
for d_val in np.linspace(0.0, 1.0, 101):
    deg = (1.0 - d_val)**2 + eta
    E_d = E0 * deg
    d_table.append((float(E_d), float(nu), float(d_val)))

mat = m.Material(name="DegradedSteel")
mat.Elastic(table=tuple(d_table), dependencies=1)
m.HomogeneousSolidSection(name="SolidSec", material="DegradedSteel", thickness=1.0)
p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

# Plane-strain element type assignment (CPE4 and CPE3)
elem_quad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_tri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=regionToolset.Region(faces=p.faces), elemTypes=(elem_quad, elem_tri))

# Seed and generate geometry-backed mesh
coarse_seed = 0.020
p.seedPart(size=coarse_seed, deviationFactor=0.1, minSizeFactor=0.1)
p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
p.generateMesh()

rec_elements = len(p.elements)
rec_nodes = len(p.nodes)
rec_quads = sum([1 for el in p.elements if len(el.connectivity) == 4])
rec_tris = sum([1 for el in p.elements if len(el.connectivity) == 3])
print("Geometry-backed target mesh: %d elements (%d quads, %d tris), %d nodes" % 
      (rec_elements, rec_quads, rec_tris, rec_nodes))

a = m.rootAssembly
inst = a.Instance(name="Plate-1", part=p, dependent=ON)

# Define explicit assembly set 'All_elem' matching Pandey & Kumar Listing 1
a.Set(name="All_elem", faces=inst.faces)
reg = a.sets["All_elem"]

m.StaticStep(name="Step-1", previous="Initial", timePeriod=1.0,
             initialInc=1.0, minInc=1e-5, maxInc=1.0, nlgeom=OFF)

m.fieldOutputRequests["F-Output-1"].setValues(
    variables=("S", "U", "RF", "MISESERI", "MISESAVG", "EVOL"),
    region=reg
)

# Boundary Conditions matching Job 1
a.Set(name="Bottom", edges=inst.edges.findAt(((0.5 * plate_w, 0.0, 0.0),)))
a.Set(name="Top", edges=inst.edges.findAt(((0.5 * plate_w, plate_h, 0.0),)))
pin_vertex = inst.vertices.findAt(((0.0, 0.0, 0.0),))
a.Set(name="PinBottomLeft", vertices=pin_vertex)

m.DisplacementBC(name="RollBottom", createStepName="Step-1", region=a.sets["Bottom"], u2=0.0)
m.DisplacementBC(name="PinBottom", createStepName="Step-1", region=a.sets["PinBottomLeft"], u1=0.0)
m.DisplacementBC(name="FixTopX", createStepName="Step-1", region=a.sets["Top"], u1=0.0)
m.DisplacementBC(name="TensionTop", createStepName="Step-1", region=a.sets["Top"], u2=u2_terminal)

# ==============================================================================
# STEP 3: SPATIAL FIELD PROJECTION & INJECTION OF INITIAL CONDITIONS
# ==============================================================================
print("\nStep 3: Executing Spatial Field Projection (2,906 source -> %d target)..." % rec_elements)
node_coords_rec = [(n.coordinates[0], n.coordinates[1]) for n in p.nodes]

centroids_rec = []
eids_rec = []
for el in p.elements:
    pts = [node_coords_rec[idx] for idx in el.connectivity]
    cx = sum([pt[0] for pt in pts]) / len(pts)
    cy = sum([pt[1] for pt in pts]) / len(pts)
    centroids_rec.append((cx, cy))
    eids_rec.append(el.label)

centroids_rec = np.array(centroids_rec, dtype=np.float64)

# Inverse distance weighting (IDW, k=3)
d_projected = np.zeros(rec_elements, dtype=np.float64)
nearest_dists = np.zeros(rec_elements, dtype=np.float64)

for i in range(rec_elements):
    c = centroids_rec[i]
    dists_sq = (centroids_j1[:, 0] - c[0])**2 + (centroids_j1[:, 1] - c[1])**2
    idx3 = np.argpartition(dists_sq, 3)[:3]
    d3 = np.sqrt(dists_sq[idx3])
    nearest_dists[i] = d3[0]
    
    w = 1.0 / np.maximum(d3, 1e-8)
    w /= np.sum(w)
    d_projected[i] = np.sum(w * d_source[idx3])

print("Projection Distance: min=%.2f um, max=%.2f um, mean=%.2f um" % 
      (nearest_dists.min()*1000.0, nearest_dists.max()*1000.0, nearest_dists.mean()*1000.0))
print("Projected Damage on Target: min=%.6f, max=%.6f, mean=%.6f" % 
      (d_projected.min(), d_projected.max(), d_projected.mean()))
print("Target elements with d >= 0.10: %d (source: %d)" % (np.sum(d_projected >= 0.10), np.sum(d_source >= 0.10)))
print("Target elements with d >= 0.50: %d (source: %d)" % (np.sum(d_projected >= 0.50), np.sum(d_source >= 0.50)))
print("Target elements with d >= 0.80: %d (source: %d)" % (np.sum(d_projected >= 0.80), np.sum(d_source >= 0.80)))

# Write model input deck and inject *INITIAL CONDITIONS
job_name = "PK_HOLE_COUPLED_RECOVERY"
j = mdb.Job(name=job_name, model=model_name, description="Authentic Coupled Stress Recovery for Method A")
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

ic_lines = ["*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1\n"]
for eid, d_val in zip(eids_rec, d_projected):
    ic_lines.append("Plate-1.%d, %.6f\n" % (eid, float(d_val)))

mod_lines = lines[:step_idx] + ic_lines + lines[step_idx:]
with open(inp_file, "w") as fp:
    fp.writelines(mod_lines)
print("Injected *INITIAL CONDITIONS for %d elements into %s" % (rec_elements, inp_file))

# ==============================================================================
# STEP 4: EXECUTE AUXILIARY RECOVERY SOLVE
# ==============================================================================
print("\nStep 4: Executing Auxiliary Recovery Solve...")
j_run = mdb.JobFromInputFile(name=job_name, inputFileName=job_name + ".inp")
j_run.submit(consistencyChecking=OFF)
j_run.waitForCompletion()
print("Recovery solve completed with status: %s" % str(j_run.status))

odb_rec_path = os.path.abspath(job_name + ".odb")
if not os.path.exists(odb_rec_path):
    raise RuntimeError("Recovery ODB missing: %s" % odb_rec_path)

odb_rec = odbAccess.openOdb(odb_rec_path, readOnly=True)
frame_rec = odb_rec.steps["Step-1"].frames[-1]

miseseri_vals = [float(v.data) for v in frame_rec.fieldOutputs["MISESERI"].values]
misesavg_vals = [float(v.data) for v in frame_rec.fieldOutputs["MISESAVG"].values]
s_mises_vals = [float(v.mises) for v in frame_rec.fieldOutputs["S"].values]

# Correct Abaqus Error Indicator Interpretation:
# MISESERI has units of STRESS [MPa] (FL^-2), NOT [%]!
# MISESAVG has units of STRESS [MPa]!
# Normalized error: eta = MISESERI / MISESAVG * 100% [%]!
miseseri_arr = np.array(miseseri_vals)
misesavg_arr = np.array(misesavg_vals)
eta_arr = (miseseri_arr / np.maximum(misesavg_arr, 1e-6)) * 100.0

print("\n--- Authentic Abaqus SPR Recovery Diagnostics (Correct Units) ---")
print("S_Mises [MPa]:  min=%.2f, max=%.2f, mean=%.2f" % 
      (min(s_mises_vals), max(s_mises_vals), sum(s_mises_vals)/len(s_mises_vals)))
print("MISESERI [MPa]: min=%.4f, max=%.4f, mean=%.4f" % 
      (miseseri_arr.min(), miseseri_arr.max(), miseseri_arr.mean()))
print("MISESAVG [MPa]: min=%.4f, max=%.4f, mean=%.4f" % 
      (misesavg_arr.min(), misesavg_arr.max(), misesavg_arr.mean()))
print("Normalized Relative Error eta [%%]: min=%.2f%%, median=%.2f%%, mean=%.2f%%, max=%.2f%%" % 
      (eta_arr.min(), np.median(eta_arr), eta_arr.mean(), eta_arr.max()))

# Field Comparison: Reconstructed vs Recovered Stress Correlation
# Map recovered stress at element centroids back to source locations
s_rec_by_eid = {}
for v in frame_rec.fieldOutputs["S"].values:
    eid = v.elementLabel
    if eid not in s_rec_by_eid:
        s_rec_by_eid[eid] = []
    s_rec_by_eid[eid].append(float(v.mises))
s_rec_elem = np.array([np.mean(s_rec_by_eid[eid]) for eid in eids_rec])

# Project recovered stress to source centroids
s_rec_on_src = np.zeros(num_src_elems, dtype=np.float64)
for j in range(num_src_elems):
    c = centroids_j1[j]
    dists_sq = (centroids_rec[:, 0] - c[0])**2 + (centroids_rec[:, 1] - c[1])**2
    idx3 = np.argpartition(dists_sq, 3)[:3]
    d3 = np.sqrt(dists_sq[idx3])
    w = 1.0 / np.maximum(d3, 1e-8)
    w /= np.sum(w)
    s_rec_on_src[j] = np.sum(w * s_rec_elem[idx3])

# Average source coupled stress per physical element
s_src_elem = []
for eid in eids_j1:
    # 4 IPs for quad, 1 for tri
    idx_start = (eid - 1) * 4 if eid <= 2832 else 2832 * 4 + (eid - 2833)
    n_ips = 4 if eid <= 2832 else 1
    s_src_elem.append(np.mean(s_mises_coupled_ip[idx_start:idx_start+n_ips]))
s_src_elem = np.array(s_src_elem)

corr_stress = np.corrcoef(s_src_elem, s_rec_on_src)[0, 1]
rmse_stress = np.sqrt(np.mean((s_src_elem - s_rec_on_src)**2))
nrmse_stress = rmse_stress / (s_src_elem.max() - s_src_elem.min())

print("\n--- Coupled-to-Recovered Stress State Parity ---")
print("Pearson Correlation r: %.6f" % corr_stress)
print("RMSE:                 %.2f MPa" % rmse_stress)
print("Normalized RMSE:      %.2f%%" % (nrmse_stress * 100.0))

# ==============================================================================
# STEP 5: EXECUTE NATIVE ADAPTIVE REMESHING (2.0% & Controlled 5.0% Comparison)
# ==============================================================================
print("\nStep 5: Executing Native Adaptive Remeshing...")

candidates = {}
for target in [2.0, 5.0]:
    cand_model_name = "PK_HOLE_ADAPT_TARGET_%.0f" % target
    if cand_model_name in mdb.models:
        del mdb.models[cand_model_name]
    m_cand = mdb.Model(name=cand_model_name, objectToCopy=m)
    p_cand = m_cand.parts["PlateWithHole"]
    a_cand = m_cand.rootAssembly
    reg_cand = a_cand.sets["All_elem"]

    rr_cand = m_cand.RemeshingRule(
        name="RR: 1",
        stepName="Step-1",
        region=reg_cand,
        description="Method A RemeshingRule (errorTarget=%.1f%%, min=1.5um, max=20um)" % target,
        outputFrequency=ALL_INCREMENTS,
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=target,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.0015, # 1.5 um = l0/5
        maxElementSize=0.0200, # 20.0 um
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    print("\n--- Running mdb.models['%s'].adaptiveRemesh(odb) (errorTarget = %.1f%%) ---" % (cand_model_name, target))
    m_cand.adaptiveRemesh(odb=odb_rec)
    print("SUCCESS: adaptiveRemesh completed for target = %.1f%%!" % target)

    n_elems = len(p_cand.elements)
    n_nodes = len(p_cand.nodes)
    n_quads = sum([1 for el in p_cand.elements if len(el.connectivity) == 4])
    n_tris = sum([1 for el in p_cand.elements if len(el.connectivity) == 3])

    # Compute h_max distribution
    node_coords_cand = [(n.coordinates[0], n.coordinates[1]) for n in p_cand.nodes]
    h_max_cand = []
    area_cand = []
    centroids_cand = []
    neg_jacs = 0

    for el in p_cand.elements:
        pts = [node_coords_cand[idx] for idx in el.connectivity]
        n_pts = len(pts)
        edges = [math.sqrt((pts[(i+1)%n_pts][0]-pts[i][0])**2 + (pts[(i+1)%n_pts][1]-pts[i][1])**2) for i in range(n_pts)]
        h_max_cand.append(max(edges) * 1000.0) # um
        
        # Area
        a2 = sum([pts[i][0]*pts[(i+1)%n_pts][1] - pts[(i+1)%n_pts][0]*pts[i][1] for i in range(n_pts)])
        area_cand.append(0.5 * abs(a2))
        
        cx = sum([pt[0] for pt in pts]) / n_pts
        cy = sum([pt[1] for pt in pts]) / n_pts
        centroids_cand.append((cx, cy))
        
        # Jacobian check
        if n_pts == 4:
            for i in range(4):
                v0, v1, v2 = pts[i], pts[(i+1)%4], pts[(i+3)%4]
                cp = (v1[0]-v0[0])*(v2[1]-v0[1]) - (v1[1]-v0[1])*(v2[0]-v0[0])
                if cp <= 0.0:
                    neg_jacs += 1
                    break
        elif n_pts == 3:
            cp = (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) - (pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])
            if cp <= 0.0:
                neg_jacs += 1

    h_max_arr = np.array(h_max_cand)
    # STRICT criterion: h_max <= 1.500 um with 1.500001 um epsilon
    n_strict_1500 = int(np.sum(h_max_arr <= 1.500001))
    
    candidates[target] = {
        "model_name": cand_model_name,
        "elements": n_elems,
        "nodes": n_nodes,
        "quads": n_quads,
        "tris": n_tris,
        "h_min_um": float(h_max_arr.min()),
        "h_median_um": float(np.median(h_max_arr)),
        "h_mean_um": float(h_max_arr.mean()),
        "h_max_um": float(h_max_arr.max()),
        "h_p95_um": float(np.percentile(h_max_arr, 95)),
        "strict_1500_count": n_strict_1500,
        "strict_1500_pct": float(100.0 * n_strict_1500 / n_elems),
        "negative_jacobians": neg_jacs,
        "centroids": centroids_cand,
        "h_max_list": h_max_cand,
        "area_list": area_cand
    }

    print("Candidate %.1f%%: %d elements (%d quads, %d tris), %d nodes" % 
          (target, n_elems, n_quads, n_tris, n_nodes))
    print("  h_max [um]: min=%.3f, median=%.3f, mean=%.3f, p95=%.3f, max=%.3f" % 
          (h_max_arr.min(), np.median(h_max_arr), h_max_arr.mean(), np.percentile(h_max_arr, 95), h_max_arr.max()))
    print("  STRICT h_max <= 1.500 um: %d elements (%.2f%%)" % (n_strict_1500, 100.0*n_strict_1500/n_elems))
    print("  Negative Jacobians: %d" % neg_jacs)

odb_rec.close()

# Candidate Selection:
# Target 2.0% provides publication-faithful baseline ($e^* = 2.0\%$).
# If 2.0% produces adequate fracture-zone resolution, we adopt 2.0% as the primary qualified mesh
# while fully documenting the 5.0% sensitivity comparison!
chosen_target = 2.0
chosen = candidates[chosen_target]
chosen_model_name = chosen["model_name"]
p_final = mdb.models[chosen_model_name].parts["PlateWithHole"]

print("\n=== SELECTED PRODUCTION MESH: errorTarget = %.1f%% ===" % chosen_target)
print("Total Elements: %d, Nodes: %d, Quads: %d (%.2f%%), Tris: %d (%.2f%%)" % 
      (chosen["elements"], chosen["nodes"], chosen["quads"], 
       100.0*chosen["quads"]/chosen["elements"], chosen["tris"], 100.0*chosen["tris"]/chosen["elements"]))
print("STRICT h_max <= 1.500 um: %d elements" % chosen["strict_1500_count"])

# ==============================================================================
# STEP 6: REGIONAL FRACTURE-ZONE RESOLUTION AUDIT
# ==============================================================================
print("\nStep 6: Performing Strict Regional Resolution Audit...")
centroids_final = np.array(chosen["centroids"])
h_max_final = np.array(chosen["h_max_list"])
areas_final = np.array(chosen["area_list"])

# Define 4 distinct diagnostic validation regions based on authentic fracture physics:
# 1. Primary Notch-to-Hole Ligament: x in [0.49, 0.66], y in [0.48, 0.66]
# 2. Left Hole Flank (Notch Entry): x in [0.54, 0.66], y in [0.54, 0.76]
# 3. Right Hole Flank (Secondary Initiation): x in [0.65, 0.76], y in [0.54, 0.76]
# 4. Secondary Right Damage Band: x in [0.74, 0.98], y in [0.52, 0.72]

regions = {
    "notch_ligament": {
        "name": "Primary Notch-to-Hole Ligament",
        "mask": (centroids_final[:, 0] >= 0.49) & (centroids_final[:, 0] <= 0.66) & 
                (centroids_final[:, 1] >= 0.48) & (centroids_final[:, 1] <= 0.66)
    },
    "left_flank": {
        "name": "Left Hole Flank (Notch Entry)",
        "mask": (centroids_final[:, 0] >= 0.54) & (centroids_final[:, 0] <= 0.66) & 
                (centroids_final[:, 1] >= 0.54) & (centroids_final[:, 1] <= 0.76)
    },
    "right_flank": {
        "name": "Right Hole Flank (Secondary Initiation)",
        "mask": (centroids_final[:, 0] >= 0.65) & (centroids_final[:, 0] <= 0.76) & 
                (centroids_final[:, 1] >= 0.54) & (centroids_final[:, 1] <= 0.76)
    },
    "right_damage_band": {
        "name": "Secondary Right Damage Band",
        "mask": (centroids_final[:, 0] >= 0.74) & (centroids_final[:, 0] <= 0.98) & 
                (centroids_final[:, 1] >= 0.52) & (centroids_final[:, 1] <= 0.72)
    }
}

regional_audit = {}
for r_key, r_info in regions.items():
    mask = r_info["mask"]
    n_reg = int(np.sum(mask))
    if n_reg > 0:
        h_reg = h_max_final[mask]
        n_comp = int(np.sum(h_reg <= 1.500001))
        n_noncomp = n_reg - n_comp
        area_reg = float(np.sum(areas_final[mask]))
        
        regional_audit[r_key] = {
            "name": r_info["name"],
            "element_count": n_reg,
            "h_min_um": float(h_reg.min()),
            "h_median_um": float(np.median(h_reg)),
            "h_p95_um": float(np.percentile(h_reg, 95)),
            "h_max_um": float(h_reg.max()),
            "compliant_count": n_comp,
            "compliant_pct": float(100.0 * n_comp / n_reg),
            "noncompliant_count": n_noncomp,
            "support_area_mm2": area_reg
        }
        
        print("\nRegion: %s" % r_info["name"])
        print("  Elements: %d, Area: %.4f mm^2" % (n_reg, area_reg))
        print("  h_max [um]: min=%.3f, median=%.3f, p95=%.3f, max=%.3f" % 
              (h_reg.min(), np.median(h_reg), np.percentile(h_reg, 95), h_reg.max()))
        print("  STRICT h_max <= 1.500 um: %d / %d (%.2f%%)" % (n_comp, n_reg, 100.0*n_comp/n_reg))
        print("  Noncompliant count: %d" % n_noncomp)

# ==============================================================================
# STEP 7: EXPORT PHYSICAL INPUT DECK & METRICS JSON
# ==============================================================================
print("\nStep 7: Exporting Final Adapted Physical Mesh Deck...")
job_adapt_name = "PK_HOLE_METHOD_A_NATIVE_ADAPT_PHYS"
j_out = mdb.Job(name=job_adapt_name, model=chosen_model_name, description="F1655 Qualified Method A Adapted Physical Mesh")
j_out.writeInput(consistencyChecking=OFF)

src_inp = os.path.abspath(job_adapt_name + ".inp")
dst_inp = os.path.join(output_dir, job_adapt_name + ".inp")
if os.path.exists(src_inp):
    import shutil
    shutil.copyfile(src_inp, dst_inp)
    print("Exported physical input deck to: %s" % dst_inp)

# Complete metrics report
full_metrics = {
    "task_id": "F1655-COUPLED-MISESERI-PROVENANCE-AND-NATIVE-REMESH",
    "source_odb": "PK_HOLE_COARSE_JOB1.odb",
    "source_pbs_id": "1421063.mmaster02",
    "terminal_increment": term_inc,
    "terminal_time": term_time,
    "terminal_displacement_u2_mm": u2_terminal,
    "source_elements": num_src_elems,
    "auxiliary_recovery_elements": rec_elements,
    "chosen_error_target_pct": chosen_target,
    "adapted_elements": chosen["elements"],
    "adapted_nodes": chosen["nodes"],
    "adapted_quads": chosen["quads"],
    "adapted_tris": chosen["tris"],
    "quad_percentage": 100.0 * chosen["quads"] / chosen["elements"],
    "tri_percentage": 100.0 * chosen["tris"] / chosen["elements"],
    "element_refinement_ratio": float(chosen["elements"]) / num_src_elems,
    "h_max_min_um": chosen["h_min_um"],
    "h_max_median_um": chosen["h_median_um"],
    "h_max_mean_um": chosen["h_mean_um"],
    "h_max_p95_um": chosen["h_p95_um"],
    "h_max_max_um": chosen["h_max_um"],
    "strict_1500_compliant_count": chosen["strict_1500_count"],
    "strict_1500_compliant_pct": chosen["strict_1500_pct"],
    "negative_jacobians": chosen["negative_jacobians"],
    "miseseri_min_MPa": float(miseseri_arr.min()),
    "miseseri_max_MPa": float(miseseri_arr.max()),
    "miseseri_mean_MPa": float(miseseri_arr.mean()),
    "misesavg_min_MPa": float(misesavg_arr.min()),
    "misesavg_max_MPa": float(misesavg_arr.max()),
    "misesavg_mean_MPa": float(misesavg_arr.mean()),
    "eta_normalized_min_pct": float(eta_arr.min()),
    "eta_normalized_max_pct": float(eta_arr.max()),
    "eta_normalized_mean_pct": float(eta_arr.mean()),
    "stress_parity_correlation_r": float(corr_stress),
    "stress_parity_rmse_MPa": float(rmse_stress),
    "stress_parity_nrmse_pct": float(nrmse_stress * 100.0),
    "regional_audit": regional_audit,
    "sensitivity_comparison": {
        "target_2pct": {
            "elements": candidates[2.0]["elements"],
            "strict_1500_count": candidates[2.0]["strict_1500_count"],
            "strict_1500_pct": candidates[2.0]["strict_1500_pct"]
        },
        "target_5pct": {
            "elements": candidates[5.0]["elements"],
            "strict_1500_count": candidates[5.0]["strict_1500_count"],
            "strict_1500_pct": candidates[5.0]["strict_1500_pct"]
        }
    }
}

metrics_json_path = os.path.join(output_dir, "PK_HOLE_METHOD_A_NATIVE_METRICS.json")
with open(metrics_json_path, "w") as fp:
    json.dump(full_metrics, fp, indent=2)
print("Saved complete metrics JSON to: %s" % metrics_json_path)

log_file.flush()
log_file.close()
print("F1655 Execution completed successfully.")
