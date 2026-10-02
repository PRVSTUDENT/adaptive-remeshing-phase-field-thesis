#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract max d and H from PK_M1_MINI_SERIAL.odb using abaqus python."""

import sys
from odbAccess import openOdb

def extract_dh(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['Step-1']
    last_frame = step.frames[-1]

    print("Frame %d, time = %f" % (last_frame.frameId, last_frame.frameValue))

    # Check SDVs
    if 'SDV1' in last_frame.fieldOutputs:
        sdv1 = last_frame.fieldOutputs['SDV1']
        sdv2 = last_frame.fieldOutputs['SDV2']
        max_d = max(val.data for val in sdv1.values)
        max_h = max(val.data for val in sdv2.values)
        print("Max Phase d (SDV1) = %.8e" % max_d)
        print("Max History H (SDV2) = %.8e" % max_h)
    else:
        print("SDV1 not found in fieldOutputs:", last_frame.fieldOutputs.keys())

    odb.close()

if __name__ == "__main__":
    odb_p = sys.argv[1] if len(sys.argv) > 1 else "PK_M1_MINI_SERIAL.odb"
    extract_dh(odb_p)
