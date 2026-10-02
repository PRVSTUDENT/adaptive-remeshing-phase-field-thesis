#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect Frame 17 field outputs in 1390447.mmaster02.odb and prepare identity state extraction
"""

from odbAccess import openOdb
import os
import sys

odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
odb = openOdb(odb_path, readOnly=True)

step = odb.steps['ShearStep']
frame = step.frames[17]

print("================================================================================")
print("FRAME 17 FIELD OUTPUTS")
print("================================================================================")
for k, v in frame.fieldOutputs.items():
    print("  Field: %-15s | Type: %-15s | Description: %s" % (k, v.type, v.description))

# Inspect U field
u_field = frame.fieldOutputs['U']
print("\nU field value count: %d" % len(u_field.values))
sample_nodes = [1, 4513, 8979, 99999]
for val in u_field.values:
    if val.nodeLabel in sample_nodes:
        print("  Node %-5d: U1 = %12.6e, U2 = %12.6e, DOF3 (d) = %12.6e" % (
            val.nodeLabel, val.data[0], val.data[1], val.data[2] if len(val.data)>=3 else 0.0))

# Inspect SDV field if present
if 'SDV' in frame.fieldOutputs:
    sdv_field = frame.fieldOutputs['SDV']
    print("\nSDV field value count: %d" % len(sdv_field.values))
elif 'SDV_H' in frame.fieldOutputs:
    sdv_field = frame.fieldOutputs['SDV_H']
    print("\nSDV_H field value count: %d" % len(sdv_field.values))
else:
    print("\nChecking all SDV variations...")
    for k in frame.fieldOutputs:
        if 'SDV' in k or 'VAR' in k:
            print("  Found: %s" % k)

odb.close()
