#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit spatial mismatch in u1, u2, nodal d, and 4-GP committed H at handoff,
Step 2 (MECH_EQUILIBRATION), and Step 3 (PHASE_RELEASE).
"""

from odbAccess import openOdb
import os
import sys
import math
import json

def audit_spatial_transfer():
    h1_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    ctrl_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"
    trans_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    odb_h1 = openOdb(h1_path, readOnly=True)
    odb_ctrl = openOdb(ctrl_path, readOnly=True)
    odb_trans = openOdb(trans_path, readOnly=True)
    
    print("=== SPATIAL MISMATCH & POINTWISE STATE-TRANSFER DIAGNOSTICS ===")
    
    # 1. Handoff State Evaluation (H1 Frame 29 vs Native Step 1 vs Stage-D Step 1)
    f29_h1 = odb_h1.steps['ShearStep'].frames[29]
    f1_ctrl = odb_ctrl.steps['STATE_INSTALL'].frames[-1]
    f1_trans = odb_trans.steps['STATE_INSTALL'].frames[-1]
    
    # Get notch tip region nodes (x in [-0.5, 0.5], y in [0.4, 0.6])
    inst_h1 = odb_h1.rootAssembly.instances['PART-1-1'] if 'PART-1-1' in odb_h1.rootAssembly.instances else list(odb_h1.rootAssembly.instances.values())[0]
    inst_trans = odb_trans.rootAssembly.instances['PART-1-1'] if 'PART-1-1' in odb_trans.rootAssembly.instances else list(odb_trans.rootAssembly.instances.values())[0]
    
    # Build spatial KD-tree or nearest-neighbor map for displacement and d comparison
    h1_nodes = {}
    for n in inst_h1.nodes:
        h1_nodes[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))
        
    u_h1 = {v.nodeLabel: (float(v.data[0]), float(v.data[1]), float(v.data[2])) for v in f29_h1.fieldOutputs['U'].values if len(v.data) >= 3}
    u_trans = {v.nodeLabel: (float(v.data[0]), float(v.data[1]), float(v.data[2])) for v in f1_trans.fieldOutputs['U'].values if len(v.data) >= 3}
    
    # Sample 10 points along the ligament (y = 0.5, x from 0.0 to 1.5)
    print("\n1. Pointwise Nodal State Mismatch Along Ligament (y = 0.5 mm):")
    print("%-8s | %-12s | %-12s | %-12s | %-12s | %-12s" % ("x (mm)", "H1 u1 (mm)", "Trans u1 (mm)", "H1 d", "Trans d", "d Diff"))
    print("-" * 75)
    
    def find_nearest_node(nodes_dict, target_x, target_y):
        best_nid = None
        best_dist = 1e9
        for nid, (x, y) in nodes_dict.items():
            dist = (x - target_x)**2 + (y - target_y)**2
            if dist < best_dist:
                best_dist = dist
                best_nid = nid
        return best_nid, math.sqrt(best_dist)

    trans_nodes = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_trans.nodes}
    
    for x_target in [0.0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.25, 1.5]:
        nid_h1, dist_h1 = find_nearest_node(h1_nodes, x_target, 0.5)
        nid_t, dist_t = find_nearest_node(trans_nodes, x_target, 0.5)
        
        u1_h = u_h1[nid_h1][0] if nid_h1 in u_h1 else 0.0
        d_h = u_h1[nid_h1][2] if nid_h1 in u_h1 else 0.0
        
        u1_t = u_trans[nid_t][0] if nid_t in u_trans else 0.0
        d_t = u_trans[nid_t][2] if nid_t in u_trans else 0.0
        
        print("%-8.2f | %-12.6f | %-12.6f | %-12.6f | %-12.6f | %+12.6f" % (
            x_target, u1_h, u1_t, d_h, d_t, d_t - d_h))

    # 2. Stage-to-Stage Jump Evaluation
    print("\n2. Stage-to-Stage Reaction & Phase-Field Jump Analysis:")
    
    s1_t = odb_trans.steps['STATE_INSTALL'].frames[-1]
    s2_t = odb_trans.steps['MECH_EQUILIBRATION'].frames[-1]
    s3_t = odb_trans.steps['PHASE_RELEASE'].frames[-1]
    
    def get_rp_and_d(frame, rp_id=99999):
        rp_rf = 0.0
        d_max = 0.0
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == rp_id:
                    rp_rf = float(v.data[0])
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if len(v.data) >= 3 and float(v.data[2]) > d_max:
                    d_max = float(v.data[2])
        return rp_rf, d_max

    rf_s1, d_s1 = get_rp_and_d(s1_t)
    rf_s2, d_s2 = get_rp_and_d(s2_t)
    rf_s3, d_s3 = get_rp_and_d(s3_t)
    
    print("Stage-D Transfer Staged Evolution:")
    print("  Step 1 (STATE_INSTALL)     : RP RF1 = %.6f kN | d_max = %.6f" % (rf_s1, d_s1))
    print("  Step 2 (MECH_EQUILIBRATION): RP RF1 = %.6f kN | d_max = %.6f | Delta RF1 = %+.6f kN | Delta d = %+.6f" % (
        rf_s2, d_s2, rf_s2 - rf_s1, d_s2 - d_s1))
    print("  Step 3 (PHASE_RELEASE)     : RP RF1 = %.6f kN | d_max = %.6f | Delta RF1 = %+.6f kN | Delta d = %+.6f" % (
        rf_s3, d_s3, rf_s3 - rf_s2, d_s3 - d_s2))
        
    s1_c = odb_ctrl.steps['STATE_INSTALL'].frames[-1]
    s2_c = odb_ctrl.steps['MECH_EQUILIBRATION'].frames[-1]
    s3_c = odb_ctrl.steps['PHASE_RELEASE'].frames[-1]
    
    rf_c1, d_c1 = get_rp_and_d(s1_c, rp_id=12383)
    rf_c2, d_c2 = get_rp_and_d(s2_c, rp_id=12383)
    rf_c3, d_c3 = get_rp_and_d(s3_c, rp_id=12383)
    
    print("\nNative Bounded Control Staged Evolution:")
    print("  Step 1 (STATE_INSTALL)     : RP RF1 = %.6f kN | d_max = %.6f" % (rf_c1, d_c1))
    print("  Step 2 (MECH_EQUILIBRATION): RP RF1 = %.6f kN | d_max = %.6f | Delta RF1 = %+.6f kN | Delta d = %+.6f" % (
        rf_c2, d_c2, rf_c2 - rf_c1, d_c2 - d_c1))
    print("  Step 3 (PHASE_RELEASE)     : RP RF1 = %.6f kN | d_max = %.6f | Delta RF1 = %+.6f kN | Delta d = %+.6f" % (
        rf_c3, d_c3, rf_c3 - rf_c2, d_c3 - d_c2))

    odb_h1.close()
    odb_ctrl.close()
    odb_trans.close()

if __name__ == "__main__":
    audit_spatial_transfer()
