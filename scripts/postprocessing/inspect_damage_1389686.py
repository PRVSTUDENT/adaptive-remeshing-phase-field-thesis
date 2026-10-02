#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect nodal U components in 1389686.odb
"""

import os
import sys
import numpy as np
from odbAccess import openOdb

def main():
    odb_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    frame_last = step.frames[-1]
    
    u_field = frame_last.fieldOutputs['U']
    d_vals = []
    
    for v in u_field.values:
        if v.nodeLabel == 12383: continue
        # Check DOF 3 or max component
        if len(v.data) >= 3:
            d_vals.append(v.data[2])
            
    print("Total nodes with len(data)>=3: %d" % len(d_vals))
    if d_vals:
        print("Min d: %s, Max d: %s" % (min(d_vals), max(d_vals)))
        
    odb.close()

if __name__ == "__main__":
    main()
