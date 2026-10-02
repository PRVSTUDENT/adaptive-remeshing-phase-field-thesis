#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic audit of H1 donor provenance (1389686.mmaster02) and 1390279 state files
"""

import os
import sys
import struct
import json
import numpy as np
from odbAccess import openOdb

def audit_provenance():
    h1_odb_path = "models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.odb"
    
    print("================================================================================")
    print("1. AUDITING 1389686.mmaster02 ODB FRAMES")
    print("================================================================================")
    odb_h1 = openOdb(h1_odb_path, readOnly=True)
    step = odb_h1.steps['ShearStep']
    rp_id = 99999
    
    print("Total frames in ShearStep: %d" % len(step.frames))
    print("%-6s | %-6s | %-12s | %-16s | %-16s | %-12s" % (
        "Frame", "Inc", "Step Time", "RP U1 (mm)", "RP RF1 (kN)", "d_max"))
    print("-" * 80)
    
    for f_idx, frame in enumerate(step.frames):
        step_time = float(frame.frameValue)
        inc_num = frame.incrementNumber
        rp_u1 = 0.0
        rp_rf1 = 0.0
        d_max = 0.0
        
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == rp_id:
                    rp_u1 = float(v.data[0])
                if len(v.data) >= 3:
                    d_val = float(v.data[2])
                    if d_val > d_max:
                        d_max = d_val
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == rp_id:
                    rp_rf1 = float(v.data[0])
                    
        # Filter to frames around U1 = 0.010 mm
        if 0.0090 <= rp_u1 <= 0.0115 or f_idx in [13, 14, 15, 28, 29, 30]:
            print("%-6d | %-6d | %-12.6f | %-16.10f | %-+16.6f | %-12.6f" % (
                f_idx, inc_num, step_time, rp_u1, rp_rf1, d_max))
                
    odb_h1.close()

    print("\n================================================================================")
    print("2. AUDITING 1390279 STATE GENERATION MANIFEST & BINARY")
    print("================================================================================")
    m279_manifest_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/manifest.json"
    if os.path.exists(m279_manifest_path):
        with open(m279_manifest_path, 'r') as fp:
            manifest_279 = json.load(fp)
        print("1390279 Manifest:\n%s" % json.dumps(manifest_279, indent=2))
        
    m279_bin_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin"
    with open(m279_bin_path, 'rb') as fp:
        rec1_len = struct.unpack('i', fp.read(4))[0]
        rec1_bytes = fp.read(rec1_len)
        rec1_end = struct.unpack('i', fp.read(4))[0]
        phase_bin_279 = np.frombuffer(rec1_bytes, dtype=np.float64).reshape((100000, 4), order='F')

        rec2_len = struct.unpack('i', fp.read(4))[0]
        rec2_bytes = fp.read(rec2_len)
        rec2_end = struct.unpack('i', fp.read(4))[0]
        h_bin_279 = np.frombuffer(rec2_bytes, dtype=np.float64).reshape((100000, 4), order='F')

    print("\n1390279 Binary State File Statistics:")
    print("  Phase record max (elements 1..8836) : %.8f" % np.max(phase_bin_279[:8836, :]))
    print("  Phase record min (elements 1..8836) : %.8f" % np.min(phase_bin_279[:8836, :]))
    print("  History record max (elements 1..8836): %.8f" % np.max(h_bin_279[:8836, :]))
    print("  History record min (elements 1..8836): %.8f" % np.min(h_bin_279[:8836, :]))

if __name__ == "__main__":
    audit_provenance()
