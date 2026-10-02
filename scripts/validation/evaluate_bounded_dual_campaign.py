#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scientific Evaluation of Bounded Dual Campaign:
1. Native Bounded Control (1390278.mmaster02)
2. Stage-D Nonmatching Bounded Transfer (1390279.mmaster02)
against Canonical H1 Reference (1389686.mmaster02).
"""

from odbAccess import openOdb
import sys
import math

def evaluate():
    h1_ref_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    native_ctrl_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"
    staged_trans_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    print("================================================================================")
    print("SCIENTIFIC EVALUATION: BOUNDED DUAL-JOB CAMPAIGN VS CANONICAL H1")
    print("================================================================================")
    
    # 1. Open ODBs
    odb_ref = openOdb(h1_ref_path, readOnly=True)
    odb_ctrl = openOdb(native_ctrl_path, readOnly=True)
    odb_trans = openOdb(staged_trans_path, readOnly=True)
    
    # 2. Extract H1 Reference Frame 29
    f29_ref = odb_ref.steps['ShearStep'].frames[29]
    u_f29 = f29_ref.fieldOutputs['U']
    d_max_ref29 = max(v.data[2] for v in u_f29.values if len(v.data) >= 3)
    rf_pos_ref29 = sum(v.data[0] for v in f29_ref.fieldOutputs['RF'].values if v.data[0] > 0)
    print("\n--- CANONICAL H1 REFERENCE (Frame 29, U1 = 0.010143 mm) ---")
    print("  Reference RF1 sum = %.6f kN" % rf_pos_ref29)
    print("  Reference d_max   = %.6f" % d_max_ref29)

    # 3. Evaluate Native Control (1390278)
    print("\n--- 1. NATIVE BOUNDED CONTROL (1390278.mmaster02) ---")
    prev_d_ctrl = {}
    min_delta_d_ctrl = 1e9
    violations_ctrl = 0
    d_max_steps_ctrl = {}
    rf1_steps_ctrl = {}
    
    for s_name in ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']:
        if s_name in odb_ctrl.steps:
            step = odb_ctrl.steps[s_name]
            d_max_s = 0.0
            rf1_s = 0.0
            for frame in step.frames:
                if 'U' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['U'].values:
                        nid = v.nodeLabel
                        if len(v.data) >= 3:
                            d_val = v.data[2]
                            if d_val > d_max_s:
                                d_max_s = d_val
                            if nid in prev_d_ctrl:
                                delta = d_val - prev_d_ctrl[nid]
                                if delta < min_delta_d_ctrl:
                                    min_delta_d_ctrl = delta
                                if delta < -1.0e-6:
                                    violations_ctrl += 1
                            prev_d_ctrl[nid] = d_val
                if 'RF' in frame.fieldOutputs:
                    rf1_s = sum(v.data[0] for v in frame.fieldOutputs['RF'].values if v.data[0] > 0)
            d_max_steps_ctrl[s_name] = d_max_s
            rf1_steps_ctrl[s_name] = rf1_s
            print("  Step %-20s: Frames = %3d | RF1 = %.6f kN | max d = %.6f" % (
                s_name, len(step.frames), rf1_s, d_max_s))
            
    print("  Native Control Irreversibility: min(Delta d) = %+.6e | Violations (< -1e-6) = %d" % (
        min_delta_d_ctrl, violations_ctrl))

    # 4. Evaluate Stage-D Nonmatching Transfer (1390279)
    print("\n--- 2. STAGE-D NONMATCHING BOUNDED TRANSFER (1390279.mmaster02) ---")
    prev_d_trans = {}
    min_delta_d_trans = 1e9
    violations_trans = 0
    d_max_steps_trans = {}
    rf1_steps_trans = {}
    
    for s_name in ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']:
        if s_name in odb_trans.steps:
            step = odb_trans.steps[s_name]
            d_max_s = 0.0
            rf1_s = 0.0
            for frame in step.frames:
                if 'U' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['U'].values:
                        nid = v.nodeLabel
                        if len(v.data) >= 3:
                            d_val = v.data[2]
                            if d_val > d_max_s:
                                d_max_s = d_val
                            if nid in prev_d_trans:
                                delta = d_val - prev_d_trans[nid]
                                if delta < min_delta_d_trans:
                                    min_delta_d_trans = delta
                                if delta < -1.0e-6:
                                    violations_trans += 1
                            prev_d_trans[nid] = d_val
                if 'RF' in frame.fieldOutputs:
                    rf1_s = sum(v.data[0] for v in frame.fieldOutputs['RF'].values if v.data[0] > 0)
            d_max_steps_trans[s_name] = d_max_s
            rf1_steps_trans[s_name] = rf1_s
            print("  Step %-20s: Frames = %3d | RF1 = %.6f kN | max d = %.6f" % (
                s_name, len(step.frames), rf1_s, d_max_s))
            
    print("  Stage-D Transfer Irreversibility: min(Delta d) = %+.6e | Violations (< -1e-6) = %d" % (
        min_delta_d_trans, violations_trans))

    # 5. Extract Continuation Curves & Parity
    print("\n--- 3. CONTINUATION CURVES & COMPARISON ---")
    
    def extract_cont_curve(odb):
        step = odb.steps['CONTINUATION']
        curve = []
        for f in step.frames:
            rf_sum = sum(v.data[0] for v in f.fieldOutputs['RF'].values if v.data[0] > 0) if 'RF' in f.fieldOutputs else 0.0
            u_max = max(v.data[0] for v in f.fieldOutputs['U'].values) if 'U' in f.fieldOutputs else 0.0
            d_max = max(v.data[2] for v in f.fieldOutputs['U'].values if len(v.data) >= 3) if 'U' in f.fieldOutputs else 0.0
            curve.append((u_max, rf_sum, d_max))
        return curve

    c_ctrl = extract_cont_curve(odb_ctrl)
    c_trans = extract_cont_curve(odb_trans)
    
    peak_ctrl = max(c_ctrl, key=lambda x: x[1])
    peak_trans = max(c_trans, key=lambda x: x[1])
    
    print("  Native Control Peak:  RF1 = %.6f kN at U1 = %.6f mm | terminal d_max = %.6f" % (
        peak_ctrl[1], peak_ctrl[0], c_ctrl[-1][2]))
    print("  Stage-D Transfer Peak: RF1 = %.6f kN at U1 = %.6f mm | terminal d_max = %.6f" % (
        peak_trans[1], peak_trans[0], c_trans[-1][2]))
    
    diff_peak = (peak_trans[1] - peak_ctrl[1]) / peak_ctrl[1] * 100.0
    print("  Peak Load Parity Error (Stage-D vs Native Bounded Control): %+.2f%%" % diff_peak)
    print("  Terminal Phase Field Bound Check: Native = %.6f (<= 1.0), Stage-D = %.6f (<= 1.0)" % (
        c_ctrl[-1][2], c_trans[-1][2]))

    odb_ref.close()
    odb_ctrl.close()
    odb_trans.close()

if __name__ == "__main__":
    evaluate()
