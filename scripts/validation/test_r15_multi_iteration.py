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

all_nodes = set(d0_dict.keys())
active_set = set(all_nodes)
free_set = set()

B_max = 20
tau_release = 5.0e-8 # kN/mm
tau_heal = 1.0e-8
max_outer_iters = 4

print("=================================================================")
print("R15 AUTONOMOUS RANKED BATCH MULTI-ITERATION SIMULATION")
print("=================================================================")
print("Total nodes: %d | B_max: %d | tau_release: %.1e kN/mm" % (len(all_nodes), B_max, tau_release))

history = []

for outer_iter in range(1, max_outer_iters + 1):
    print("\n-------------------------------------------------------------")
    print("OUTER ACTIVE-SET ITERATION %d (Active: %d, Free: %d)" % (outer_iter, len(active_set), len(free_set)))
    print("-------------------------------------------------------------")
    
    # 1. Write active_set_boundary_cards.inc
    inc_filename = "active_set_boundary_cards_it%d.inc" % outer_iter
    with open(inc_filename, 'w') as f:
        for nid in sorted(active_set):
            f.write("%d, 3, 3, %.8f\n" % (nid, d0_dict[nid]))
            
    # 2. Write INP deck
    job_name = "TEST_R15_IT%d" % outer_iter
    with open('M1_C3_ACTIVE_SET_R14_CONTINUATION.inp') as f:
        inp_content = f.read()
    inp_content = inp_content.replace('active_set_boundary_cards.inc', inc_filename)
    inp_content = inp_content.replace('1.0, 1.0, 1.0E-5, 1.0', '1.0, 1.0, 1.0E-8, 1.0')
    inp_content = inp_content.replace('name=Inc1-Coupled, nlgeom=NO, inc=25', 'name=Inc1-Coupled, nlgeom=NO, inc=200')
    
    inp_file = "%s.inp" % job_name
    with open(inp_file, 'w') as f:
        f.write(inp_content)
        
    # 3. Execute Abaqus
    cmd = "abaqus job=%s input=%s user=f42_unified_12dof_active_set_uel.for cpus=1 interactive" % (job_name, inp_file)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    
    if p.returncode != 0:
        print("FAIL: Abaqus returned non-zero exit code %d" % p.returncode)
        break
        
    # 4. Check ODB
    odb_file = "%s.odb" % job_name
    if not os.path.exists(odb_file):
        print("FAIL: ODB file %s not found" % odb_file)
        break
        
    odb = openOdb(odb_file)
    step2 = odb.steps['Inc1-Coupled']
    last_frame = step2.frames[-1]
    
    u = last_frame.fieldOutputs['U']
    rf = last_frame.fieldOutputs['RF']
    
    u_dict = {val.nodeLabel: val.data for val in u.values}
    rf_dict = {val.nodeLabel: val.data for val in rf.values}
    
    u2_rp = u_dict.get(999999, (0, 0, 0))[1]
    rf2_rp = rf_dict.get(999999, (0, 0, 0))[1] * 1000.0 # N
    
    # Check kinematic accuracy
    target_u2 = 0.00196610735
    u_err = abs(u2_rp - target_u2)
    print("Reached U2 RP:   %.10f mm (Error: %.2e mm)" % (u2_rp, u_err))
    print("Reaction RF2:    %.6f N" % rf2_rp)
    
    # Check max damage and healing
    d_max = max(u_dict[n][2] for n in all_nodes if n in u_dict)
    print("Max damage:      %.6f" % d_max)
    
    # KKT evaluation
    violating_active = []
    for nid in active_set:
        rf3 = rf_dict.get(nid, (0, 0, 0))[2]
        if rf3 < -tau_release:
            violating_active.append((nid, rf3))
            
    violating_active.sort(key=lambda x: x[1]) # most negative first
    
    # Check free nodes for healing
    healing_free = []
    for nid in free_set:
        d_val = u_dict.get(nid, (0, 0, 0))[2]
        delta_d = d_val - d0_dict[nid]
        if delta_d < -tau_heal:
            healing_free.append(nid)
            
    print("Violating active nodes (RF3 < -%.1e): %d" % (tau_release, len(violating_active)))
    print("Healing free nodes:                    %d" % len(healing_free))
    
    history.append({
        'iter': outer_iter,
        'rf2': rf2_rp,
        'u2': u2_rp,
        'd_max': d_max,
        'violating_count': len(violating_active),
        'healing_count': len(healing_free)
    })
    
    odb.close()
    
    if len(violating_active) == 0 and len(healing_free) == 0:
        print("\n>>> ACTIVE-SET BINARY CLOSURE ACHIEVED AT OUTER ITERATION %d! <<<" % outer_iter)
        break
        
    # Select up to B_max nodes to release
    to_release = set(n for n, r in violating_active[:B_max])
    print("Releasing top %d nodes with strongest driving forces:" % len(to_release))
    for n, r in violating_active[:min(5, len(violating_active))]:
        print("  Node %5d: RF3 = %14.6e kN/mm, d0 = %.5f" % (n, r, d0_dict[n]))
        
    active_set.difference_update(to_release)
    free_set.update(to_release)
    
    # Reactivate any healing nodes
    if len(healing_free) > 0:
        print("Reactivating %d healing nodes" % len(healing_free))
        free_set.difference_update(healing_free)
        active_set.update(healing_free)

print("\n=================================================================")
print("SUMMARY OF OUTER ITERATIONS")
print("=================================================================")
for h in history:
    print("Iter %d: RF2 = %9.4f N | U2 = %.10f mm | d_max = %.6f | Violating: %d | Healing: %d" % (
        h['iter'], h['rf2'], h['u2'], h['d_max'], h['violating_count'], h['healing_count']
    ))
