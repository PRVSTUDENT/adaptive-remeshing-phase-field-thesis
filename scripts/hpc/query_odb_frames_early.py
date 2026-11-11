"""
scripts/hpc/query_odb_frames_early.py
Check early frames of Step-1 in M1_PK_F1714_JOB2_ADAPTED.odb
"""
import sys
from odbAccess import openOdb

odb = openOdb("M1_PK_F1714_JOB2_ADAPTED.odb", readOnly=True)
try:
    step = odb.steps['Step-1']
    for idx in range(min(10, len(step.frames))):
        f = step.frames[idx]
        u_val = f.fieldOutputs['U'].values[0].data
        rf_val = f.fieldOutputs['RF'].values[0].data
        print("Frame %d (t=%.6e): U=%s, RF=%s" % (idx, f.frameValue, list(u_val), list(rf_val)))
finally:
    odb.close()
