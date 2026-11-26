from __future__ import print_function
import sys
from odbAccess import openOdb

odb = openOdb('models/complex_mixed_load/run_campaign/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1.odb')
step = odb.steps['Step-1']
print('Total frames: %d' % len(step.frames))
for f_idx, f in enumerate(step.frames):
    keys = f.fieldOutputs.keys()
    sdv1 = f.fieldOutputs['SDV1'] if 'SDV1' in keys else None
    rf = f.fieldOutputs['RF'] if 'RF' in keys else None
    u = f.fieldOutputs['U'] if 'U' in keys else None
    max_d = max(v.data for v in sdv1.values) if sdv1 else 0.0
    rf_rp = [v.data for v in rf.values if v.nodeLabel == 999999] if rf else None
    u_rp = [v.data for v in u.values if v.nodeLabel == 999999] if u else None
    rf2 = rf_rp[0][1] if rf_rp else 0.0
    rf1 = rf_rp[0][0] if rf_rp else 0.0
    uy = u_rp[0][1] if u_rp else 0.0
    ux = u_rp[0][0] if u_rp else 0.0
    print('Frame %d (Inc %d, time=%.4f): uy=%.6f, ux=%.6f, RF2=%.4f, RF1=%.4f, max_d=%.4f' % (
        f_idx, f.incrementNumber, f.frameValue, uy, ux, rf2, rf1, max_d
    ))

# Check where max damage is at last frame
last_f = step.frames[-1]
if 'SDV1' in last_f.fieldOutputs.keys():
    sdv1 = last_f.fieldOutputs['SDV1']
    max_val = -1.0
    max_elem = -1
    for v in sdv1.values:
        if v.data > max_val:
            max_val = v.data
            max_elem = v.elementLabel
    print('Last frame max damage = %.4f at element %d' % (max_val, max_elem))

odb.close()
