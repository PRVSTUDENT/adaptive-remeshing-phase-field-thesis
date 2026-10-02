#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trace where 0.00350319 came from
"""

import os
from odbAccess import openOdb

odb_path = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.odb"
odb = openOdb(odb_path, readOnly=True)
last_frame = odb.steps['ShearStep'].frames[-1]

for v in last_frame.fieldOutputs['RF'].values:
    if abs(v.data[0] - 0.00350319) < 0.0001:
        print("Found node with 0.00350319:", v.nodeLabel, v.data)
        
print("Node 99999 RF in last frame:", [v.data for v in last_frame.fieldOutputs['RF'].values if v.nodeLabel == 99999])
print("Node 99999 U in last frame:", [v.data for v in last_frame.fieldOutputs['U'].values if v.nodeLabel == 99999])
odb.close()
