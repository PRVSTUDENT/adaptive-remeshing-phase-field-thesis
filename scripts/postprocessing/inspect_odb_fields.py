from __future__ import print_function
import sys
from odbAccess import openOdb

odb = openOdb('PK_HOLE_METHOD_A_PROD.odb', readOnly=True)
step = odb.steps[odb.steps.keys()[0]]
frame = step.frames[-1]

print("Available fieldOutputs:")
for k in frame.fieldOutputs.keys():
    print(" -", k)

for f_name in frame.fieldOutputs.keys():
    fo = frame.fieldOutputs[f_name]
    print("Field %s: type=%s, locations=%s, num_values=%d" % (f_name, fo.type, fo.locations, len(fo.values)))
    if len(fo.values) > 0:
        v0 = fo.values[0]
        print("   sample elementLabel=%s, data=%s" % (getattr(v0, 'elementLabel', None), getattr(v0, 'data', None)))
        v_last = fo.values[-1]
        print("   last sample elementLabel=%s, data=%s" % (getattr(v_last, 'elementLabel', None), getattr(v_last, 'data', None)))

odb.close()
