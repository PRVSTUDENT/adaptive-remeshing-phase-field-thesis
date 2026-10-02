#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect ODB fields for Job 1389686.mmaster02
"""

import os
import sys
from odbAccess import openOdb

def main():
    odb_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    
    print("Total frames: %d" % len(step.frames))
    frame_last = step.frames[-1]
    print("Last frame time: %s" % frame_last.frameValue)
    print("Field outputs: %s" % frame_last.fieldOutputs.keys())
    
    # Check node 12383
    if 'U' in frame_last.fieldOutputs:
        for v in frame_last.fieldOutputs['U'].values:
            if v.nodeLabel == 12383:
                print("Node 12383 U: %s" % str(v.data))
    if 'RF' in frame_last.fieldOutputs:
        for v in frame_last.fieldOutputs['RF'].values:
            if v.nodeLabel == 12383:
                print("Node 12383 RF: %s" % str(v.data))
                
    odb.close()

if __name__ == "__main__":
    main()
