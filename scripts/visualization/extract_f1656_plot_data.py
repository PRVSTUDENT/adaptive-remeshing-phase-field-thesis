# scripts/visualization/extract_f1656_plot_data.py
"""
Extract data from donor Job 1 ODB and F1656 recovery ODB for plotting.
Run via 'abaqus python'.
"""
import os
import sys
import json
import numpy as np

try:
    import odbAccess
except ImportError:
    print("Run via 'abaqus python'.")
    sys.exit(1)

out_file = "f1656_plot_data.json"

# 1. Load Donor
odb_j1_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb")
odb_j1 = odbAccess.openOdb(odb_j1_path, readOnly=True)
inst_j1 = odb_j1.rootAssembly.instances['PART-1-1']
nodes_j1 = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_j1.nodes}

centroids_j1 = []
eids_j1 = []
for el in inst_j1.elements:
    if el.label <= 2906:
        pts = [nodes_j1[lbl] for lbl in el.connectivity]
        cx = sum([p[0] for p in pts]) / len(pts)
        cy = sum([p[1] for p in pts]) / len(pts)
        centroids_j1.append((cx, cy))
        eids_j1.append(el.label)

f_term = odb_j1.steps['Step-2'].frames[-1]
sdv1_map = {(v.elementLabel, v.integrationPoint): float(v.data) for v in f_term.fieldOutputs['SDV1'].values}
sdv15_map = {(v.elementLabel, v.integrationPoint): float(v.data) for v in f_term.fieldOutputs['SDV15'].values}
e_map = {(v.elementLabel, v.integrationPoint): v.data for v in f_term.fieldOutputs['E'].values}

E0 = 210000.0; nu = 0.3
c11 = E0 * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
c12 = E0 * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
c33 = E0 / (2.0 * (1.0 + nu))

donor_mises = {}
donor_d = {}
for (eid, ipt), eps in e_map.items():
    if (eid, ipt) not in sdv15_map or (eid, ipt) not in sdv1_map:
        continue
    g_val = sdv15_map[(eid, ipt)]
    d_val = sdv1_map[(eid, ipt)]
    e11, e22, e33, e12 = float(eps[0]), float(eps[1]), float(eps[2]), float(eps[3])
    s11 = g_val * (c11 * e11 + c12 * e22)
    s22 = g_val * (c12 * e11 + c11 * e22)
    s33 = g_val * c12 * (e11 + e22)
    s12 = g_val * (2.0 * c33 * e12)
    mises = (0.5 * ((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 + 6.0 * s12**2))**0.5
    phys_eid = eid - 2 * 2906 if eid > 2 * 2906 else eid
    donor_mises.setdefault(phys_eid, []).append(mises)
    donor_d.setdefault(phys_eid, []).append(d_val)

odb_j1.close()

donor_elem_mises = [float(np.mean(donor_mises[eid])) for eid in eids_j1]
donor_elem_d = [float(np.mean(donor_d[eid])) for eid in eids_j1]

# 2. Load Recovery
odb_rec_path = os.path.abspath("PK_HOLE_F1656_RECOVERY.odb")
odb_rec = odbAccess.openOdb(odb_rec_path, readOnly=True)
inst_rec = odb_rec.rootAssembly.instances['PLATE-1']
nodes_rec = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_rec.nodes}

centroids_rec = []
eids_rec = []
for el in inst_rec.elements:
    pts = [nodes_rec[lbl] for lbl in el.connectivity]
    cx = sum([p[0] for p in pts]) / len(pts)
    cy = sum([p[1] for p in pts]) / len(pts)
    centroids_rec.append((cx, cy))
    eids_rec.append(el.label)

f_rec = odb_rec.steps['Step-1'].frames[-1]
s_rec_by_elem = {}
for v in f_rec.fieldOutputs['S'].values:
    s_rec_by_elem.setdefault(v.elementLabel, []).append(float(v.mises))

rec_elem_mises = [float(np.mean(s_rec_by_elem[eid])) for eid in eids_rec]

fv1_by_elem = {}
if 'FV1' in f_rec.fieldOutputs:
    for v in f_rec.fieldOutputs['FV1'].values:
        fv1_by_elem.setdefault(v.elementLabel, []).append(float(v.data))
rec_elem_fv1 = [float(np.mean(fv1_by_elem[eid])) for eid in eids_rec] if fv1_by_elem else []

miseseri_vals = [float(v.data) for v in f_rec.fieldOutputs['MISESERI'].values]
misesavg_vals = [float(v.data) for v in f_rec.fieldOutputs['MISESAVG'].values]

odb_rec.close()

# Export JSON
plot_data = {
    "donor_centroids": centroids_j1,
    "donor_elem_mises": donor_elem_mises,
    "donor_elem_d": donor_elem_d,
    "rec_centroids": centroids_rec,
    "rec_elem_mises": rec_elem_mises,
    "rec_elem_fv1": rec_elem_fv1,
    "miseseri_vals": miseseri_vals,
    "misesavg_vals": misesavg_vals
}

with open(out_file, "w") as fp:
    json.dump(plot_data, fp)

print("Exported %s successfully." % out_file)
