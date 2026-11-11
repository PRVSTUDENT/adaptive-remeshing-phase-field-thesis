"""
scripts/hpc/query_odb_u_rf.py
Inspect U and RF field outputs across all nodes in M1_PK_F1714_JOB2_ADAPTED.odb
"""
import sys
import os

try:
    from odbAccess import openOdb
except ImportError:
    print("Error: odbAccess not available")
    sys.exit(1)

odb = openOdb("M1_PK_F1714_JOB2_ADAPTED.odb", readOnly=True)

try:
    print("ODB opened successfully.")
    for sname in ['Step-1', 'Step-2']:
        if sname not in odb.steps:
            continue
        step = odb.steps[sname]
        print("\n=== STEP: %s (%d frames) ===" % (sname, len(step.frames)))
        
        # Check frame 0 and last frame
        frames_to_check = [("Frame 0", step.frames[0]), ("Last Frame", step.frames[-1])]
        for fname, frame in frames_to_check:
            print("\n--- %s: time=%.4f (desc: %s) ---" % (fname, frame.frameValue, frame.description))
            for fld_name in ['U', 'RF']:
                if fld_name in frame.fieldOutputs:
                    fld = frame.fieldOutputs[fld_name]
                    vals = fld.values
                    print("Field '%s': %d values" % (fld_name, len(vals)))
                    count = 0
                    for v in vals:
                        if count < 5:
                            print("  Node %d: %s" % (v.nodeLabel, str(list(v.data))))
                            count += 1
                        else:
                            break
                    # Also find min and max of each component
                    if len(vals) > 0:
                        dim = len(vals[0].data)
                        for d in range(dim):
                            c_vals = [float(v.data[d]) for v in vals]
                            print("  Comp %d: min=%.6e, max=%.6e" % (d, min(c_vals), max(c_vals)))

finally:
    odb.close()
    print("ODB closed.")
