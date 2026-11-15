from __future__ import print_function
from odbAccess import openOdb
odb = openOdb('/scratch9/pr21vyci/runs/mode1_pk_f1776_fracture_batch/case1_mode1_edge_crack/PK_F1728_CASE_1_PROD.odb', readOnly=True)
frame = odb.steps['Step-2'].frames[-1]
print("Field output keys in last frame of Step-2:")
for k in frame.fieldOutputs.keys():
    fo = frame.fieldOutputs[k]
    print("  Key: '%s', type: %s, description: '%s'" % (k, fo.type, fo.description))
    if hasattr(fo, 'componentLabels'):
        print("    Components: %s" % str(fo.componentLabels))
odb.close()
