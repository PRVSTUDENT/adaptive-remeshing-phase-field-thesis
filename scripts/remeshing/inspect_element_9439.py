from __future__ import print_function
import sys
from odbAccess import openOdb

odb_path = '/scratch9/pr21vyci/runs/mode1_method_a_hole_f1685_prod/M1_HOLE_F1685_COMBINED_PROD.odb'
odb = openOdb(odb_path, readOnly=True)
step = odb.steps['Step-2']
print('Step-2 total frames: %d' % len(step.frames))

target_eid = 43138 + 9439  # Layer 3 UMAT element

for f_idx in [195, 196, 197, 198, 199, 200, 201]:
    f = step.frames[f_idx]
    sdv1 = f.fieldOutputs['SDV1']
    vals = [v for v in sdv1.values if v.elementLabel == target_eid]
    print('Frame %d (Inc %d, time=%.6e):' % (f_idx, f.incrementNumber, f.frameValue))
    for v in vals:
        print('   IP %d: d=%.8f' % (v.integrationPoint, v.data))

odb.close()
