#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect kinematic boundary conditions, equations, and node sets across:
1. Canonical H1 Reference (M2CORR_H1_FREEU2_FULL_U050)
2. Native Bounded Control (M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL)
3. Stage-D Nonmatching Transfer (M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL)
"""

from odbAccess import openOdb
import os
import sys

def inspect_models():
    h1_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    ctrl_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"
    trans_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    print("=== INSPECTING MODEL BOUNDARIES & EQUATIONS ===")
    
    for name, p in [("H1_REF", h1_path), ("NATIVE_CTRL", ctrl_path), ("STAGED_TRANS", trans_path)]:
        odb = openOdb(p, readOnly=True)
        print("\nModel: %s" % name)
        print("Steps: %s" % list(odb.steps.keys()))
        inst = odb.rootAssembly.instances['PART-1-1'] if 'PART-1-1' in odb.rootAssembly.instances else odb.rootAssembly.instances[list(odb.rootAssembly.instances.keys())[0]]
        print("Instance: %s, Nodes: %d, Elements: %d" % (inst.name, len(inst.nodes), len(inst.elements)))
        print("Node Sets: %s" % list(odb.rootAssembly.nodeSets.keys()))
        
        # Check Node Set Top/Bottom/RP
        for ns_name in ['TOP_EDGES', 'BOTTOM_EDGES', 'RP', 'TOP_NODES', 'BOT_NODES', 'REF_POINT']:
            if ns_name in odb.rootAssembly.nodeSets:
                ns = odb.rootAssembly.nodeSets[ns_name]
                print("  NodeSet %s: %d nodes" % (ns_name, len(ns.nodes)))
                
        # Check Frame 0 / First Frame Reactions
        step0 = list(odb.steps.values())[0]
        f0 = step0.frames[-1]
        print("Step %s Last Frame (Value: %f):" % (step0.name, f0.frameValue))
        if 'RF' in f0.fieldOutputs:
            rf = f0.fieldOutputs['RF']
            pos_rf = [v for v in rf.values if v.data[0] > 0]
            neg_rf = [v for v in rf.values if v.data[0] < 0]
            sum_pos = sum(v.data[0] for v in pos_rf)
            sum_neg = sum(v.data[0] for v in neg_rf)
            print("  Total Positive RF1 Sum: %f kN (%d nodes)" % (sum_pos, len(pos_rf)))
            print("  Total Negative RF1 Sum: %f kN (%d nodes)" % (sum_neg, len(neg_rf)))
            # Show top 5 positive and negative nodes
            pos_rf.sort(key=lambda x: x.data[0], reverse=True)
            neg_rf.sort(key=lambda x: x.data[0])
            print("  Top 3 Positive RF1 Nodes:")
            for v in pos_rf[:3]:
                print("    Node %d: RF1 = %f kN" % (v.nodeLabel, v.data[0]))
            print("  Top 3 Negative RF1 Nodes:")
            for v in neg_rf[:3]:
                print("    Node %d: RF1 = %f kN" % (v.nodeLabel, v.data[0]))
        odb.close()

if __name__ == "__main__":
    inspect_models()
