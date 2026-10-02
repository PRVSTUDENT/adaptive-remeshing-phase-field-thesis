#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deep Forensic Audit of Early State Ingestion and Damage Evolution for 1390439.mmaster02.
"""

from odbAccess import openOdb
import os
import sys
import json
import math

def audit_early_state():
    pkg_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    odb_path = os.path.join(pkg_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb")
    msg_path = os.path.join(pkg_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.msg")
    dat_path = os.path.join(pkg_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.dat")
    out_path = os.path.join(pkg_dir, "pbs.out")
    err_path = os.path.join(pkg_dir, "pbs.err")
    for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")

    h1_odb_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"

    print("================================================================================")
    print("TASK F268: FORENSIC AUDIT OF EARLY STATE & VIRGIN INGESTION (JOB 1390439)")
    print("================================================================================")

    # 1. Inspect Fortran UEL code for file open paths
    print("\n--- 1. UEL UEXTERNALDB (LOP=0) FILE INGESTION AUDIT ---")
    with open(for_path, 'r') as fp:
        lines = fp.readlines()
        
    print("Inspecting f44_mixed_uel_restart_stateinit.for LOP=0 logic:")
    for idx, l in enumerate(lines[30:65], start=31):
        print("  Line %2d: %s" % (idx, l.rstrip()))

    # Check if state load message was emitted in msg or pbs.out
    print("\nChecking solver output streams for state-load messages:")
    for p, name in [(out_path, "pbs.out"), (msg_path, "M2CORR_STAGE_D_...msg"), (dat_path, "M2CORR_STAGE_D_...dat")]:
        if os.path.exists(p):
            with open(p, 'r') as fp:
                content = fp.read()
            if "SUCCESS: Imported restart state" in content:
                print("  [CRITICAL FINDING] %s contains: 'SUCCESS: Imported restart state from Stage-D state file'" % name)
            elif "WARNING: State file" in content:
                print("  %s contains: 'WARNING: State file STAGE_D_COMMITTED_STATE.bin NOT FOUND! Zeroing state.'" % name)
            else:
                print("  %s does not contain explicit state-load banner." % name)

    # 2. Inspect First 15 ODB Frames of 1390439
    print("\n--- 2. EARLY INCREMENT TRAJECTORY AUDIT (FRAMES 0 TO 15) ---")
    odb = openOdb(odb_path, readOnly=True)
    inst = odb.rootAssembly.instances['PART-1-1'] if 'PART-1-1' in odb.rootAssembly.instances else list(odb.rootAssembly.instances.values())[0]
    
    node_coords = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst.nodes if n.label != 99999}
    step = odb.steps['ShearStep']
    
    print("%-5s | %-5s | %-12s | %-14s | %-14s | %-10s | %-10s | %-8s | %-8s | %-16s" % (
        "Frame", "Inc", "Step Time", "Phys U1 (mm)", "RP RF1 (kN)", "d_min", "d_max", "N(d<=0)", "N(d>=1)", "Max d Node (x, y)"))
    print("-" * 118)

    first_nonzero_inc = None
    first_d1_inc = None

    for f_idx in range(min(16, len(step.frames))):
        f = step.frames[f_idx]
        inc_num = f.incrementNumber
        t_val = float(f.frameValue)
        phys_u1 = t_val * 0.050

        rp_rf1 = 0.0
        if 'RF' in f.fieldOutputs:
            for v in f.fieldOutputs['RF'].values:
                if v.nodeLabel == 99999:
                    rp_rf1 = float(v.data[0])

        d_vals = {}
        if 'U' in f.fieldOutputs:
            for v in f.fieldOutputs['U'].values:
                if v.nodeLabel in node_coords:
                    d_val = float(v.data[2]) if len(v.data) >= 3 else 0.0
                    d_vals[v.nodeLabel] = d_val

        d_min = min(d_vals.values()) if d_vals else 0.0
        d_max = max(d_vals.values()) if d_vals else 0.0
        
        # count bounds
        n_lower = sum(1 for v in d_vals.values() if v <= 1e-6)
        n_upper = sum(1 for v in d_vals.values() if v >= 0.999)

        max_nid = max(d_vals, key=d_vals.get) if d_vals else None
        max_coord_str = "(%+.3f, %+.3f)" % node_coords[max_nid] if max_nid else "N/A"

        if d_max > 1e-6 and first_nonzero_inc is None:
            first_nonzero_inc = (inc_num, phys_u1, d_max)

        if d_max >= 0.999 and first_d1_inc is None:
            first_d1_inc = (inc_num, phys_u1)

        print("%-5d | %-5d | %-12.6f | %-14.6f | %-+14.6f | %-10.6f | %-10.6f | %-8d | %-8d | %-6d %-16s" % (
            f_idx, inc_num, t_val, phys_u1, rp_rf1, d_min, d_max, n_lower, n_upper, max_nid if max_nid else 0, max_coord_str))

    print("\nSummary of Early Damage Evolution:")
    if first_nonzero_inc:
        print("  First increment with d > 0: Inc %d at Phys U1 = %.6f mm (d_max = %.6f)" % first_nonzero_inc)
    if first_d1_inc:
        print("  First increment with d = 1: Inc %d at Phys U1 = %.6f mm" % first_d1_inc)

    # 3. Compare with Canonical H1 Continuous Run (1389686)
    print("\n--- 3. COMPARISON WITH CANONICAL H1 CONTINUOUS RUN (1389686) AT LOW U1 ---")
    odb_h1 = openOdb(h1_odb_path, readOnly=True)
    step_h1 = odb_h1.steps['ShearStep']

    print("%-5s | %-5s | %-12s | %-14s | %-14s | %-10s | %-10s" % (
        "Frame", "Inc", "Step Time", "Phys U1 (mm)", "H1 RF1 (kN)", "H1 d_min", "H1 d_max"))
    print("-" * 80)

    for f_idx in range(min(12, len(step_h1.frames))):
        f = step_h1.frames[f_idx]
        inc_num = f.incrementNumber
        t_val = float(f.frameValue)
        phys_u1 = 0.0
        rf1 = 0.0
        d_max = 0.0
        d_min = 1.0

        if 'U' in f.fieldOutputs:
            for v in f.fieldOutputs['U'].values:
                if v.nodeLabel == 12383:
                    phys_u1 = float(v.data[0])
                if len(v.data) >= 3:
                    dv = float(v.data[2])
                    if dv > d_max: d_max = dv
                    if dv < d_min: d_min = dv

        if 'RF' in f.fieldOutputs:
            for v in f.fieldOutputs['RF'].values:
                if v.nodeLabel == 12383:
                    rf1 = float(v.data[0])

        print("%-5d | %-5d | %-12.6f | %-14.6f | %-+14.6f | %-10.6f | %-10.6f" % (
            f_idx, inc_num, t_val, phys_u1, rf1, d_min if d_min <= 1.0 else 0.0, d_max))

    odb.close()
    odb_h1.close()

if __name__ == "__main__":
    audit_early_state()
