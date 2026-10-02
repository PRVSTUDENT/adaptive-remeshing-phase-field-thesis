#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect H1 source state at Frame 29 (U1 = 0.010143 mm).
"""

import os
import sys
import numpy as np
from odbAccess import openOdb

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

odb_path = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
inp_path = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")

print("Opening ODB: %s" % odb_path)
odb = openOdb(odb_path, readOnly=True)
step = odb.steps[odb.steps.keys()[0]]

target_u1 = 0.0101433
best_frame = min(step.frames, key=lambda f: abs(float(f.frameValue) - target_u1))
f_idx = step.frames.index(best_frame) if hasattr(step.frames, 'index') else 29
for i, f in enumerate(step.frames):
    if f == best_frame:
        f_idx = i
        break

print("Matched Frame %d at Step Time = %.6f (target = %.6f)" % (f_idx, float(best_frame.frameValue), target_u1))

# Inspect displacement and phase fields
u_field = best_frame.fieldOutputs['U']
rf_field = best_frame.fieldOutputs['RF']

u1_vals = []
u2_vals = []
d_vals = []

for v in u_field.values:
    data = v.data
    u1_vals.append(float(data[0]))
    u2_vals.append(float(data[1]))
    if len(data) >= 3:
        d_vals.append(float(data[2]))

print("Displacement U1 range: [%.6f, %.6f] mm" % (min(u1_vals), max(u1_vals)))
print("Displacement U2 range: [%.6f, %.6f] mm" % (min(u2_vals), max(u2_vals)))
print("Phase Field  d  range: [%.6f, %.6f]" % (min(d_vals), max(d_vals)))

# Inspect RF1
rf1_sum_pos = sum([float(v.data[0]) for v in rf_field.values if float(v.data[0]) > 0])
print("Sum positive RF1: %.6f kN" % rf1_sum_pos)

odb.close()
