# -*- coding: utf-8 -*-
import os
import sys
from odbAccess import openOdb

odb_paths = [
    r"models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb",
    r"models/pandey_kumar_mode1/210_f1719_five_hole_coarse_pfm/PK_F1719_COARSE_PFM.odb",
    r"models/pandey_kumar_mode1/209_f1718_five_hole_recovery/PK_F1718_RECOVERY_PHYS.odb",
    r"models/pandey_kumar_mode1/211_f1719_coarse_recovery/PK_F1719_REC_STATE2_PHYS.odb"
]

for p in odb_paths:
    print("=" * 60)
    print("Checking: %s" % p)
    if not os.path.exists(p):
        print("  File not found!")
        continue
    odb = openOdb(p, readOnly=True)
    print("  Root assembly instances: %s" % odb.rootAssembly.instances.keys())
    for step_name, step in odb.steps.items():
        print("  Step: %s, Total frames: %d" % (step_name, len(step.frames)))
        times = [f.frameValue for f in step.frames]
        print("    Time range: min=%.6f, max=%.6f" % (min(times), max(times)))
        # Check first, middle, last frame fields
        for idx in [0, len(step.frames)//2, len(step.frames)-1]:
            f = step.frames[idx]
            has_miseseri = 'MISESERI' in f.fieldOutputs
            has_misesavg = 'MISESAVG' in f.fieldOutputs
            has_s = 'S' in f.fieldOutputs
            has_sdv = 'SDV' in f.fieldOutputs
            print("    Frame %3d (t=%.4f): MISESERI=%s, MISESAVG=%s, S=%s, SDV=%s" %
                  (idx, f.frameValue, has_miseseri, has_misesavg, has_s, has_sdv))
    odb.close()
