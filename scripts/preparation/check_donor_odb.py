#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper to check donor extraction
"""
import os
from odbAccess import openOdb

def check_donor():
    donor_odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
    odb = openOdb(donor_odb_path, readOnly=True)
    step = odb.steps.values()[0]
    frame = step.frames[17]
    print("Frame value: %s" % frame.frameValue)
    print("Available Field Outputs:")
    for k in sorted(frame.fieldOutputs.keys()):
        print("  - %s" % k)
    odb.close()

if __name__ == "__main__":
    check_donor()
