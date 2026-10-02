#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odbAccess import openOdb
import os

odbs = [
    ("M2REF_H1", "models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.odb"),
    ("M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL", "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"),
    ("M2CORR_H1_FREEU2_FULL_U050", "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
]

for name, path in odbs:
    if os.path.exists(path):
        odb = openOdb(path, readOnly=True)
        print("================================================================================")
        print("ODB: %s (%s)" % (name, path))
        print("================================================================================")
        for s_name, step in odb.steps.items():
            print("Step: %s | Total Frames: %d" % (s_name, len(step.frames)))
            for f_idx, f in enumerate(step.frames):
                t = float(f.frameValue)
                inc = f.incrementNumber
                rp_u1 = 0.0
                d_max = 0.0
                if 'U' in f.fieldOutputs:
                    for v in f.fieldOutputs['U'].values:
                        if v.nodeLabel == 99999:
                            rp_u1 = float(v.data[0])
                        if len(v.data)>=3:
                            if float(v.data[2]) > d_max:
                                d_max = float(v.data[2])
                if abs(rp_u1 - 0.0101433) < 0.001 or f_idx in [14, 28, 29, 30]:
                    print("  Frame %-4d | Inc %-4d | Time %-10.6f | RP U1 %-14.8f | d_max %-10.6f" % (
                        f_idx, inc, t, rp_u1, d_max))
        odb.close()
