import sys
import numpy as np
from odbAccess import openOdb

odb_path = '/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r14/M1_C3_ACTIVE_SET_R14_IT1.odb'
odb = openOdb(odb_path)
step = odb.steps['Inc1-Coupled']
frame = step.frames[-1]
rf = frame.fieldOutputs['RF']
root_assembly = odb.rootAssembly
instance = root_assembly.instances.values()[0]

node_coords = {n.label: n.coordinates for n in instance.nodes}

rf3_vals = []
for val in rf.values:
    rf3_vals.append((val.nodeLabel, val.data[2]))

rf3_vals.sort(key=lambda x: x[1])

print('=== Nodes with RF3 < -5.0e-8 kN/mm ===')
count = 0
for n, r in rf3_vals:
    if r < -5.0e-8:
        count += 1
        x, y, z = node_coords[n]
        print('Node %5d: X = %8.5f, Y = %8.5f | RF3 = %14.6e kN/mm' % (n, x, y, r))

print('Total nodes with RF3 < -5.0e-8: %d' % count)

print('\n=== Nodes with RF3 < -1.0e-8 kN/mm ===')
count_1e8 = sum(1 for n, r in rf3_vals if r < -1.0e-8)
print('Total nodes with RF3 < -1.0e-8: %d' % count_1e8)

odb.close()
