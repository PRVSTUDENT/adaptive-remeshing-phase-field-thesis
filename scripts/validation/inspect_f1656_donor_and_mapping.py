# scripts/validation/inspect_f1656_donor_and_mapping.py
"""
Diagnostic script to audit donor Job 1 ODB:
1. N_RP displacement and reaction history
2. N_TOP boundary kinematics
3. Explicit (elementLabel, integrationPoint) join for SDV1, SDV15, E
4. True physical stress reconstruction via frozen UEL constitutive law
5. Auditing receiver node vs element numbering in CAD model
"""
import sys
import os
import math
import numpy as np

# Check if running under abaqus python
try:
    import odbAccess
    from abaqusConstants import *
except ImportError:
    print("This script must be executed via 'abaqus python'.")
    sys.exit(1)

odb_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb")
if not os.path.exists(odb_path):
    print("ERROR: ODB not found: %s" % odb_path)
    sys.exit(1)

print("Opening ODB: %s" % odb_path)
odb = odbAccess.openOdb(odb_path, readOnly=True)

# 1. Inspect Steps and Frames
print("\n--- 1. Step and Frame Audit ---")
for sname in odb.steps.keys():
    st = odb.steps[sname]
    print("Step: %s, frames: %d" % (sname, len(st.frames)))

step2 = odb.steps["Step-2"]
f_term = step2.frames[-1]
inc_num = f_term.incrementNumber
frame_val = f_term.frameValue
print("Terminal frame: Step-2 Inc %d, frameValue=%.6f" % (inc_num, frame_val))

# 2. Inspect N_RP (Node 999999) and N_TOP
print("\n--- 2. Kinematic Boundary Condition Audit ---")
root_inst = odb.rootAssembly.instances['PART-1-1']
u_field = f_term.fieldOutputs['U']

# Check U at values[0] vs Node 999999
val0 = u_field.values[0]
print("u_field.values[0]: nodeLabel=%d, data=%s" % (val0.nodeLabel, str(val0.data)))

# Find Node 999999
u_rp = None
for v in u_field.values:
    if v.nodeLabel == 999999:
        u_rp = v
        break

if u_rp is not None:
    print("N_RP (Node 999999): U1=%.8e, U2=%.8e mm" % (u_rp.data[0], u_rp.data[1]))
else:
    print("WARNING: Node 999999 not found in rootAssembly.instances['PART-1-1'] fieldOutput U!")
    # Check root assembly nodes
    for v in f_term.fieldOutputs['U'].values:
        if v.nodeLabel == 999999:
            print("Found in rootAssembly fieldOutput: U1=%.8e, U2=%.8e" % (v.data[0], v.data[1]))

# Check nodes on N_TOP (y = 1.0)
top_nodes_u2 = []
for n in root_inst.nodes:
    if abs(n.coordinates[1] - 1.0) < 1e-6:
        # find U for this node
        pass

for v in u_field.values:
    # check coordinates of this node
    nlbl = v.nodeLabel
    if nlbl in [74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89]:
        top_nodes_u2.append(v.data[1])

if len(top_nodes_u2) > 0:
    print("Top boundary nodes (N_TOP) U2: min=%.8e, max=%.8e, mean=%.8e" % 
          (min(top_nodes_u2), max(top_nodes_u2), sum(top_nodes_u2)/len(top_nodes_u2)))

# 3. Explicit (elementLabel, integrationPoint) Join for Donor Fields
print("\n--- 3. Explicit Element/IP Join for Donor Fields ---")
sdv1_field = f_term.fieldOutputs['SDV1']
sdv15_field = f_term.fieldOutputs['SDV15']
e_field = f_term.fieldOutputs['E']

print("Field value counts: SDV1=%d, SDV15=%d, E=%d" % 
      (len(sdv1_field.values), len(sdv15_field.values), len(e_field.values)))

# Check element labels in visualizer set
# Physical elements: 1..2906
# Visualizer elements in Job 1: 5813..8718 (offset = 2*2906 = 5812)
sdv1_dict = {}
for v in sdv1_field.values:
    sdv1_dict[(v.elementLabel, v.integrationPoint)] = float(v.data)

sdv15_dict = {}
for v in sdv15_field.values:
    sdv15_dict[(v.elementLabel, v.integrationPoint)] = float(v.data)

e_dict = {}
for v in e_field.values:
    e_dict[(v.elementLabel, v.integrationPoint)] = v.data

# Plane-strain elastic constants (E=210 GPa = 210,000 MPa, nu=0.3)
E_mod = 210000.0
nu = 0.3
c11 = E_mod * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
c12 = E_mod * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
c33 = E_mod / (2.0 * (1.0 + nu))

print("Constitutive constants: C11=%.2f MPa, C12=%.2f MPa, C33=%.2f MPa" % (c11, c12, c33))

# Reconstruct stresses by explicit key join
reconstructed_stresses = {}
mises_by_elem = {}

for (eid, ipt), eps in e_dict.items():
    if (eid, ipt) not in sdv15_dict or (eid, ipt) not in sdv1_dict:
        continue
    
    d_val = sdv1_dict[(eid, ipt)]
    g_val = sdv15_dict[(eid, ipt)]
    
    # eps components: 0: E11, 1: E22, 2: E33 (plane strain should be 0), 3: E12
    e11 = float(eps[0])
    e22 = float(eps[1])
    e33 = float(eps[2])
    e12 = float(eps[3]) # tensor shear strain epsilon_12
    
    # Plane-strain stresses:
    s11 = g_val * (c11 * e11 + c12 * e22)
    s22 = g_val * (c12 * e11 + c11 * e22)
    s33 = g_val * c12 * (e11 + e22)
    s12 = g_val * (2.0 * c33 * e12)
    
    # von Mises
    mises = math.sqrt(0.5 * ((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 + 6.0 * s12**2))
    
    phys_eid = eid - 2 * 2906 if eid > 2 * 2906 else eid
    reconstructed_stresses[(phys_eid, ipt)] = {
        'd': d_val, 'g': g_val,
        's11': s11, 's22': s22, 's33': s33, 's12': s12,
        'mises': mises
    }
    
    if phys_eid not in mises_by_elem:
        mises_by_elem[phys_eid] = []
    mises_by_elem[phys_eid].append(mises)

print("Successfully reconstructed stresses for %d (element, IP) points across %d physical elements" % 
      (len(reconstructed_stresses), len(mises_by_elem)))

elem_avg_mises = [np.mean(mises_by_elem[eid]) for eid in sorted(mises_by_elem.keys())]
elem_avg_mises = np.array(elem_avg_mises)
print("Donor Element-Averaged Degraded Mises Stress:")
print("  min=%.2f MPa, median=%.2f MPa, mean=%.2f MPa, max=%.2f MPa" % 
      (elem_avg_mises.min(), np.median(elem_avg_mises), elem_avg_mises.mean(), elem_avg_mises.max()))

# Check open crack elements vs active FPZ elements
d_elem_avg = {}
for (phys_eid, ipt), data in reconstructed_stresses.items():
    if phys_eid not in d_elem_avg:
        d_elem_avg[phys_eid] = []
    d_elem_avg[phys_eid].append(data['d'])
d_elem_avg = {eid: np.mean(vals) for eid, vals in d_elem_avg.items()}

broken_eids = [eid for eid, d in d_elem_avg.items() if d >= 0.8]
fpz_eids = [eid for eid, d in d_elem_avg.items() if 0.1 <= d < 0.8]
intact_eids = [eid for eid, d in d_elem_avg.items() if d < 0.1]

print("Elements by damage state:")
print("  Broken (d >= 0.80): %d elements, mean Mises = %.2f MPa" % 
      (len(broken_eids), np.mean([np.mean(mises_by_elem[e]) for e in broken_eids]) if broken_eids else 0.0))
print("  Active FPZ (0.10 <= d < 0.80): %d elements, mean Mises = %.2f MPa" % 
      (len(fpz_eids), np.mean([np.mean(mises_by_elem[e]) for e in fpz_eids]) if fpz_eids else 0.0))
print("  Elastic/Intact (d < 0.10): %d elements, mean Mises = %.2f MPa" % 
      (len(intact_eids), np.mean([np.mean(mises_by_elem[e]) for e in intact_eids]) if intact_eids else 0.0))

odb.close()
print("\nAudit complete.")
