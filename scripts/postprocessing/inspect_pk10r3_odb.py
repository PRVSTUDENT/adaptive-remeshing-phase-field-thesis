#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect fields and values in M2CORR_PK10R3_REFINED_TIP.odb.
"""

import sys
import os
from odbAccess import openOdb

odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb"
if not os.path.exists(odb_path):
    odb_path = "D:/Master thesis/Adaptive remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb"

odb = openOdb(odb_path, readOnly=True)
step = odb.steps[odb.steps.keys()[0]]
print("Step name: %s" % step.name)
print("Total frames: %d" % len(step.frames))

# Inspect frame 10, 50, and last frame
for f_idx in [1, 20, 50, len(step.frames)-1]:
    frame = step.frames[f_idx]
    print("\n--- FRAME %d (time = %f) ---" % (f_idx, frame.frameValue))
    for k in frame.fieldOutputs.keys():
        fo = frame.fieldOutputs[k]
        print("Field %s: type=%s, num_values=%d" % (k, fo.type, len(fo.values)))
        if len(fo.values) > 0:
            val0 = fo.values[0]
            print("  sample val: data=%s, node=%s, elem=%s" % (str(val0.data), getattr(val0, 'nodeLabel', None), getattr(val0, 'elementLabel', None)))

# Inspect RF and U history
print("\n--- HISTORY REGIONS ---")
for hr_k in step.historyRegions.keys():
    hr = step.historyRegions[hr_k]
    print("History Region %s: %s" % (hr_k, hr.historyOutputs.keys()))
    for ho_k in hr.historyOutputs.keys():
        ho = hr.historyOutputs[ho_k]
        data = ho.data
        if len(data) > 0:
            print("  %s: %d points, start=(%f, %f), end=(%f, %f), max_val=%f" % (
                ho_k, len(data), data[0][0], data[0][1], data[-1][0], data[-1][1], max([abs(v[1]) for v in data])))

odb.close()
