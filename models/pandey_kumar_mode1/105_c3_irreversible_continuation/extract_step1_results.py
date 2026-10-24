#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_step1_results_v4.py
Extracts RF2 at Node 999999 and d_max from SDV1 and SDV14 in Stage-A
"""
import sys
from odbAccess import openOdb

def extract():
    odb = openOdb("M1_C3_IRREV_SOLVE.odb", readOnly=True)
    step1 = odb.steps["Stage-A"]
    frame = step1.frames[-1]
    
    # 1. Reaction force at Node 999999
    rf_field = frame.fieldOutputs["RF"]
    rp_node = 999999
    rp_rf2 = None
    for v in rf_field.values:
        if v.nodeLabel == rp_node:
            rp_rf2 = v.data[1]
            print("Found RP Node %d: RF = %s" % (rp_node, str(v.data)))
            print("  --> RF2 = %f kN = %f N" % (rp_rf2, rp_rf2 * 1000.0))
            break
            
    # 2. Damage field from SDV1 and SDV14
    for var_name in ["SDV1", "SDV14"]:
        if var_name in frame.fieldOutputs:
            field = frame.fieldOutputs[var_name]
            max_d = 0.0
            min_d = 1.0
            max_d_elem = None
            for v in field.values:
                d = v.data
                if d > max_d:
                    max_d = d
                    max_d_elem = v.elementLabel
                if d < min_d:
                    min_d = d
            print("  --> %s: max = %f at Element %d, min = %f" % (var_name, max_d, max_d_elem if max_d_elem else 0, min_d))
            
    odb.close()

if __name__ == "__main__":
    extract()
