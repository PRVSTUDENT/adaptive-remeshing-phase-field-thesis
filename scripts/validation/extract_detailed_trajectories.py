#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exhaustive frame-by-frame extraction of:
1. Physical U1 (from RP node and top boundary nodes)
2. RP Reaction Force (Node 12383 for H1/Native, Node 99999 for Nonmatching)
3. Bottom boundary Reaction Force sum
4. Top boundary Reaction Force sum
5. Primary phase field d (min, max, and process zone values)
"""

from odbAccess import openOdb
import os
import sys
import json
import csv

def extract_detailed_trajectories():
    h1_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    ctrl_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"
    trans_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"

    def get_rp_and_edge_data(odb_path, rp_id, y_top=1.0, y_bot=0.0, is_restart=False):
        odb = openOdb(odb_path, readOnly=True)
        inst = odb.rootAssembly.instances['PART-1-1'] if 'PART-1-1' in odb.rootAssembly.instances else odb.rootAssembly.instances[list(odb.rootAssembly.instances.keys())[0]]
        
        # Identify top and bottom nodes from nodal coordinates
        top_nids = set()
        bot_nids = set()
        for n in inst.nodes:
            # coords
            y = n.coordinates[1]
            if abs(y - y_top) < 1e-4 and n.label != rp_id:
                top_nids.add(n.label)
            elif abs(y - y_bot) < 1e-4 and n.label != rp_id:
                bot_nids.add(n.label)
                
        frames_data = []
        step_order = ['ShearStep'] if not is_restart else ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']
        
        for s_name in step_order:
            if s_name not in odb.steps:
                continue
            step = odb.steps[s_name]
            for f_idx, f in enumerate(step.frames):
                time_step = f.frameValue
                inc_num = f.incrementNumber
                
                # U field
                rp_u1 = 0.0
                max_u1 = 0.0
                min_d = 1.0e9
                max_d = -1.0e9
                
                if 'U' in f.fieldOutputs:
                    for v in f.fieldOutputs['U'].values:
                        if v.nodeLabel == rp_id:
                            rp_u1 = v.data[0]
                        if v.data[0] > max_u1:
                            max_u1 = v.data[0]
                        if len(v.data) >= 3:
                            d = v.data[2]
                            if d < min_d: min_d = d
                            if d > max_d: max_d = d
                if min_d > 1.0e8: min_d = 0.0
                if max_d < -1.0e8: max_d = 0.0
                
                # Physical U1 definition:
                # In H1/Continuation, RP prescribes U1. For non-RP frames, max top U1 or RP U1 gives the physical displacement.
                # In H1 Frame 29, physical U1 = 0.0101433 mm.
                phys_u1 = rp_u1 if rp_u1 > 0 else max_u1
                
                # RF field
                rp_rf1 = 0.0
                top_rf1_sum = 0.0
                bot_rf1_sum = 0.0
                total_pos_rf1 = 0.0
                total_neg_rf1 = 0.0
                
                if 'RF' in f.fieldOutputs:
                    for v in f.fieldOutputs['RF'].values:
                        nid = v.nodeLabel
                        rf1 = v.data[0]
                        if rf1 > 0: total_pos_rf1 += rf1
                        elif rf1 < 0: total_neg_rf1 += rf1
                        
                        if nid == rp_id:
                            rp_rf1 = rf1
                        elif nid in top_nids:
                            top_rf1_sum += rf1
                        elif nid in bot_nids:
                            bot_rf1_sum += rf1
                            
                frames_data.append({
                    'step': s_name,
                    'frame_idx': f_idx,
                    'increment': inc_num,
                    'step_time': time_step,
                    'phys_u1': phys_u1,
                    'rp_rf1': rp_rf1,
                    'top_rf1_sum': top_rf1_sum,
                    'bot_rf1_sum': bot_rf1_sum,
                    'total_pos_rf1': total_pos_rf1,
                    'total_neg_rf1': total_neg_rf1,
                    'min_d': min_d,
                    'max_d': max_d
                })
        odb.close()
        return frames_data

    print("Extracting detailed frame data...")
    d_h1 = get_rp_and_edge_data(h1_path, rp_id=12383, is_restart=False)
    d_ctrl = get_rp_and_edge_data(ctrl_path, rp_id=12383, is_restart=True)
    d_trans = get_rp_and_edge_data(trans_path, rp_id=99999, is_restart=True)
    
    print("\n--- 1. CANONICAL H1 HANDOFF FRAME (Frame 29) ---")
    f29 = d_h1[29]
    print("Frame 29: Step Time = %f, Phys U1 = %f mm" % (f29['step_time'], f29['phys_u1']))
    print("  RP RF1 (Node 12383)    : %+f kN" % f29['rp_rf1'])
    print("  Top Edge RF1 Sum       : %+f kN" % f29['top_rf1_sum'])
    print("  Bottom Edge RF1 Sum    : %+f kN" % f29['bot_rf1_sum'])
    print("  Total Positive RF1 Sum : %+f kN" % f29['total_pos_rf1'])
    print("  Total Negative RF1 Sum : %+f kN" % f29['total_neg_rf1'])
    
    print("\n--- 2. STAGE-BY-STAGE REACTION FORCE OBSERVABLE COMPARISON ---")
    print("%-18s | %-16s | %-16s | %-16s" % ("Observable", "H1 Frame 29", "Native Control S1", "Stage-D Transfer S1"))
    print("-" * 75)
    s1_c = [f for f in d_ctrl if f['step'] == 'STATE_INSTALL'][-1]
    s1_t = [f for f in d_trans if f['step'] == 'STATE_INSTALL'][-1]
    print("%-18s | %+16.6f | %+16.6f | %+16.6f" % ("RP RF1 (kN)", f29['rp_rf1'], s1_c['rp_rf1'], s1_t['rp_rf1']))
    print("%-18s | %+16.6f | %+16.6f | %+16.6f" % ("Top Edge Sum (kN)", f29['top_rf1_sum'], s1_c['top_rf1_sum'], s1_t['top_rf1_sum']))
    print("%-18s | %+16.6f | %+16.6f | %+16.6f" % ("Bot Edge Sum (kN)", f29['bot_rf1_sum'], s1_c['bot_rf1_sum'], s1_t['bot_rf1_sum']))
    print("%-18s | %+16.6f | %+16.6f | %+16.6f" % ("Total Pos Sum", f29['total_pos_rf1'], s1_c['total_pos_rf1'], s1_t['total_pos_rf1']))

    # Save to JSON for subsequent analysis
    with open("scripts/validation/detailed_extraction_audit.json", "w") as fp:
        json.dump({'h1': d_h1, 'ctrl': d_ctrl, 'trans': d_trans}, fp, indent=2)
    print("\nDetailed extraction saved to scripts/validation/detailed_extraction_audit.json")

if __name__ == "__main__":
    extract_detailed_trajectories()
