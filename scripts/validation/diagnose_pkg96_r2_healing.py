import os
from odbAccess import openOdb

odb_path = '/scratch9/pr21vyci/runs/mode1_package96_r2_c5_transfer/M1_C5_PACKAGE96_R2_TRANSFER.odb'
odb = openOdb(odb_path, readOnly=True)

fr_s3 = odb.steps['STAGGERED_PHASE_SUBPROBLEM'].frames[-1]
fr_s4 = odb.steps['FORWARD_CONTINUATION'].frames[-1]

sdv1_s3 = fr_s3.fieldOutputs['SDV1']
sdv1_s4 = fr_s4.fieldOutputs['SDV1']

d_s3 = {(v.elementLabel, v.integrationPoint): v.data for v in sdv1_s3.values}
d_s4 = {(v.elementLabel, v.integrationPoint): v.data for v in sdv1_s4.values}

healed = []
for k in d_s3:
    diff = d_s4[k] - d_s3[k]
    if diff < -1e-6:
        healed.append((k, d_s3[k], d_s4[k], diff))

print('Total healed Gauss points: %d' % len(healed))
healed.sort(key=lambda x: x[3])
for item in healed[:15]:
    phys_eid = item[0][0] - 2 * 4440 if item[0][0] > 8880 else item[0][0]
    print('  Elem %d (Phys %d) IP %d: s3=%.6f, s4=%.6f, diff=%.6e' % (item[0][0], phys_eid, item[0][1], item[1], item[2], item[3]))
