#!/usr/bin/env python3
import sys, os
from odbAccess import openOdb

def inspect_odb():
    odb_path = "M2STATE_FRACFIX_RESTART2R4.odb"
    if not os.path.exists(odb_path):
        print "ODB not found:", odb_path
        return
    odb = openOdb(odb_path, readOnly=True)
    
    print "=== ODB STEP / FRAME AUDIT ==="
    for sname in odb.steps.keys():
        step = odb.steps[sname]
        print "Step: %s, total frames: %d" % (sname, len(step.frames))
        for f_idx, frame in enumerate(step.frames):
            if 'U' not in frame.fieldOutputs:
                print "  Frame %d: U field missing" % f_idx
                continue
            u_field = frame.fieldOutputs['U']
            values = u_field.values
            nan_u1 = 0
            nan_u2 = 0
            nan_u3 = 0
            finite_u1 = 0
            finite_u3 = 0
            u3_min = 1e9
            u3_max = -1e9
            u1_min = 1e9
            u1_max = -1e9
            for v in values:
                data = v.data
                # check u1
                if len(data) >= 1:
                    val = data[0]
                    if val != val or abs(val) > 1e10:
                        nan_u1 += 1
                    else:
                        finite_u1 += 1
                        u1_min = min(u1_min, val)
                        u1_max = max(u1_max, val)
                # check u3 (phase)
                if len(data) >= 3:
                    val = data[2]
                    if val != val or abs(val) > 1e10:
                        nan_u3 += 1
                    else:
                        finite_u3 += 1
                        u3_min = min(u3_min, val)
                        u3_max = max(u3_max, val)
            print "  Frame %d (time=%.6f): finite_U1=%d, nan_U1=%d [min=%.6e, max=%.6e] | finite_U3=%d, nan_U3=%d [min=%.6e, max=%.6e]" % (
                f_idx, frame.frameValue, finite_u1, nan_u1, u1_min, u1_max, finite_u3, nan_u3, u3_min, u3_max
            )

    odb.close()

if __name__ == '__main__':
    inspect_odb()
