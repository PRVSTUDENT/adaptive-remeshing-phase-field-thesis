from __future__ import print_function
from odbAccess import openOdb

odb = openOdb('models/complex_mixed_load/run_campaign/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1.odb')
step = odb.steps['Step-1']
f = step.frames[8] # Inc 8
u = f.fieldOutputs['U']
print('Frame 8 (Inc 8):')
# Sample displacements along x = 0 (left edge)
left_nodes = []
for v in u.values:
    if v.nodeLabel <= 5817: # physical
        left_nodes.append((v.nodeLabel, v.data[0], v.data[1]))

print('Physical nodes with U:', len(left_nodes))
# Check SDV1 values
sdv1 = f.fieldOutputs['SDV1']
top_d = sorted([(v.elementLabel, v.data) for v in sdv1.values], key=lambda x: x[1], reverse=True)[:10]
print('Top 10 element damage at Inc 8:')
for eid, d in top_d:
    print('  Elem %d: d = %.6f' % (eid, d))

# Check where these elements are
inst = odb.rootAssembly.instances['PART-1-1']
for eid, d in top_d[:3]:
    elem = inst.elements[eid - 1]
    conn = elem.connectivity
    print('Elem %d conn:' % eid, conn)

odb.close()
