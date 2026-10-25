import sys
import os
import shutil
import subprocess
import numpy as np
from odbAccess import openOdb

scratch_dir = '/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r14'
os.chdir(scratch_dir)

# Read nodal d0 from stage_a_all_d0_boundary_cards.inc
d0_dict = {}
with open('stage_a_all_d0_boundary_cards.inc') as f:
    for line in f:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            d0_dict[int(parts[0])] = float(parts[3])

# Open IT1 ODB to get RF3 from Inc1-Coupled
odb = openOdb('M1_C3_ACTIVE_SET_R14_IT1.odb')
step = odb.steps['Inc1-Coupled']
frame = step.frames[-1]
rf = frame.fieldOutputs['RF']

rf3_vals = []
for val in rf.values:
    nid = val.nodeLabel
    if nid in d0_dict:
        rf3_vals.append((nid, val.data[2]))
odb.close()

rf3_vals.sort(key=lambda x: x[1])

print("Total nodes with RF3: %d" % len(rf3_vals))
print("Top 10 most negative RF3:")
for n, r in rf3_vals[:10]:
    print("  Node %5d: RF3 = %14.6e kN/mm, d0 = %8.5f" % (n, r, d0_dict[n]))

# Test batch sizes: B_max = 20
B_max = 20
released_nodes = set(n for n, r in rf3_vals[:B_max] if r < -1e-8)
print("\nReleasing %d nodes for test trial solve..." % len(released_nodes))

# Write active_set_boundary_cards.inc excluding released_nodes
with open('test_ranked_20_boundary_cards.inc', 'w') as f:
    for nid in sorted(d0_dict.keys()):
        if nid not in released_nodes:
            f.write("%d, 3, 3, %.8f\n" % (nid, d0_dict[nid]))

# Create test input file with dt_min = 1e-8 and inc=200
with open('M1_C3_ACTIVE_SET_R14_CONTINUATION.inp') as f:
    inp_content = f.read()

# Replace active_set_boundary_cards.inc with test_ranked_20_boundary_cards.inc
inp_test = inp_content.replace('active_set_boundary_cards.inc', 'test_ranked_20_boundary_cards.inc')
# Update step 2 incrementation controls to be robust
inp_test = inp_test.replace('1.0, 1.0, 1.0E-5, 1.0', '1.0, 1.0, 1.0E-8, 1.0')
inp_test = inp_test.replace('name=Inc1-Coupled, nlgeom=NO, inc=25', 'name=Inc1-Coupled, nlgeom=NO, inc=200')

with open('TEST_RANKED_20.inp', 'w') as f:
    f.write(inp_test)

print("Running Abaqus job TEST_RANKED_20...")
cmd = "abaqus job=TEST_RANKED_20 input=TEST_RANKED_20.inp user=f42_unified_12dof_active_set_uel.for cpus=1 interactive"
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()

print("Abaqus exit code: %d" % p.returncode)

# Check sta file
if os.path.exists('TEST_RANKED_20.sta'):
    with open('TEST_RANKED_20.sta') as f:
        print("\n--- TEST_RANKED_20.sta ---")
        print(f.read())

# Check results from ODB if available
if os.path.exists('TEST_RANKED_20.odb'):
    odb = openOdb('TEST_RANKED_20.odb')
    step2 = odb.steps['Inc1-Coupled']
    last_frame = step2.frames[-1]
    u = last_frame.fieldOutputs['U']
    rf = last_frame.fieldOutputs['RF']
    
    u_dict = {val.nodeLabel: val.data for val in u.values}
    rf_dict = {val.nodeLabel: val.data for val in rf.values}
    
    rf2_rp = rf_dict.get(999999, (0, 0, 0))[1] * 1000.0
    u2_rp = u_dict.get(999999, (0, 0, 0))[1]
    
    print("\n--- ODB Extraction Results ---")
    print("Reached U2 RP:   %.10f mm (Target: 0.00196610735 mm)" % u2_rp)
    print("Final RF2 RP:     %.6f N" % rf2_rp)
    
    # Check damage on released nodes
    print("\nReleased Nodes Damage Evolution:")
    for n in sorted(released_nodes):
        d_new = u_dict.get(n, (0, 0, 0))[2]
        d_init = d0_dict[n]
        delta_d = d_new - d_init
        rf3_new = rf_dict.get(n, (0, 0, 0))[2]
        print("Node %5d: d0=%.6f -> d=%.6f (delta_d=%+10.6f) | RF3=%14.6e" % (
            n, d_init, d_new, delta_d, rf3_new
        ))
    odb.close()
