import os
from odbAccess import openOdb

odb_path = '/scratch9/pr21vyci/runs/mode1_package96_r2_c5_transfer/M1_C5_PACKAGE96_R2_TRANSFER.odb'
odb = openOdb(odb_path, readOnly=True)

fr = odb.steps['FORWARD_CONTINUATION'].frames[-1]
for k in fr.fieldOutputs.keys():
    fo = fr.fieldOutputs[k]
    print("Field %s: type=%s, desc=%s, components=%s" % (k, fo.type, fo.description, str(fo.componentLabels)))

# Check if there are other fields or if node values have dof 3
u = fr.fieldOutputs['U']
print("U values length: %d" % len(u.values))
for i in range(10):
    v = u.values[i]
    print("  Node %d: data=%s" % (v.nodeLabel, str(v.data)))
