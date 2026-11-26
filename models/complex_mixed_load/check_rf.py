from __future__ import print_function
from odbAccess import openOdb

odb = openOdb('models/complex_mixed_load/run_campaign/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1.odb')
step = odb.steps['Step-1']
f = step.frames[1]
rf = f.fieldOutputs['RF']
v = rf.values[0]
print('Node:', v.nodeLabel, 'Data:', list(v.data))
odb.close()
