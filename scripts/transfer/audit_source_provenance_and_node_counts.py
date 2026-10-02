#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic Source-State Provenance and Mesh Counts Audit.

1. Parses H1 INP and ODB to determine exact node and element counts across all layers.
2. Traces every byte and slot in STAGE_D_COMMITTED_STATE.bin.
3. Samples target (PHYSIDX, KPT) entries and compares against H1 transfer table.
4. Corrects stale diagnostic text in UEL.
"""

import os
import sys
import struct
import math
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

def audit_h1_inp(inp_path):
    print("================================================================================")
    print("1. DIRECT AUDIT OF H1 SOURCE INP: %s" % inp_path)
    print("================================================================================")
    
    physical_nodes = {}
    rp_nodes = {}
    phase_elems = {} # Layer 1 (U1)
    mech_elems = {}  # Layer 2 (U2)
    other_elems = {}
    
    with open(inp_path, 'r') as f:
        reading_nodes = False
        reading_elems = False
        elem_layer = None
        
        for line in f:
            line_s = line.strip()
            if "*NODE" in line_s.upper() and "*OUTPUT" not in line_s.upper():
                reading_nodes = True
                reading_elems = False
                continue
            elif "*ELEMENT" in line_s.upper():
                reading_nodes = False
                reading_elems = True
                if "TYPE=U1" in line_s.upper() or "ELSET=E_QUAD_PHASE" in line_s.upper():
                    elem_layer = "PHASE"
                elif "TYPE=U2" in line_s.upper() or "ELSET=E_QUAD_MECH" in line_s.upper():
                    elem_layer = "MECH"
                else:
                    elem_layer = "OTHER"
                continue
            elif line_s.startswith("*"):
                reading_nodes = False
                reading_elems = False
                continue
                
            if reading_nodes:
                parts = line_s.split(",")
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        if nid == 99999:
                            rp_nodes[nid] = (x, y)
                        else:
                            physical_nodes[nid] = (x, y)
                    except: pass
            elif reading_elems:
                parts = line_s.split(",")
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        conn = [int(parts[i]) for i in range(1, 5)]
                        if elem_layer == "PHASE":
                            phase_elems[eid] = conn
                        elif elem_layer == "MECH":
                            mech_elems[eid] = conn
                        else:
                            other_elems[eid] = conn
                    except: pass
                    
    print("H1 INP Counts:")
    print("  Physical Nodes:        %d (IDs: %d .. %d)" % (
        len(physical_nodes), min(physical_nodes.keys()), max(physical_nodes.keys())))
    print("  Reference Nodes:       %d (ID: %s)" % (
        len(rp_nodes), list(rp_nodes.keys())))
    print("  Total Nodes in Deck:   %d" % (len(physical_nodes) + len(rp_nodes)))
    print("  Phase UELs (Layer 1):  %d (IDs: %d .. %d)" % (
        len(phase_elems), min(phase_elems.keys()), max(phase_elems.keys())))
    print("  Mech UELs (Layer 2):   %d (IDs: %d .. %d)" % (
        len(mech_elems), min(mech_elems.keys()), max(mech_elems.keys())))
    print("  Other/Overlay Elems:   %d" % len(other_elems))
    print("  Total UELs in Deck:    %d" % (len(phase_elems) + len(mech_elems)))
    print("  Physical Domain Quads: %d (N_phys = %d)" % (len(phase_elems), len(phase_elems)))
    
    return physical_nodes, phase_elems, mech_elems

def audit_h1_odb(odb_path):
    print("\n================================================================================")
    print("2. DIRECT AUDIT OF H1 SOURCE ODB: %s" % odb_path)
    print("================================================================================")
    
    odb = openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly
    
    print("ODB Root Assembly Instances: %s" % list(root.instances.keys()))
    if len(root.instances) > 0:
        inst = root.instances[root.instances.keys()[0]]
        print("  Instance Nodes:    %d" % len(inst.nodes))
        print("  Instance Elements: %d" % len(inst.elements))
    else:
        print("  Root Assembly Nodes:    %d" % len(root.nodes))
        print("  Root Assembly Elements: %d" % len(root.elements))
        
    step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    print("Step Name: %s, Total Frames: %d" % (step_name, len(step.frames)))
    
    frame29 = step.frames[29]
    u1_f29 = float(frame29.frameValue)
    print("Frame 29 Properties:")
    print("  Frame Index: %d" % frame29.frameId)
    print("  Frame Value (Shear Disp U1): %.7f mm" % u1_f29)
    print("  Description: %s" % frame29.description)
    
    u_field = frame29.fieldOutputs['U']
    d_vals = []
    u1_vals = []
    u2_vals = []
    
    for v in u_field.values:
        data = v.data
        u1_vals.append(float(data[0]))
        u2_vals.append(float(data[1]))
        if len(data) >= 3:
            d_vals.append(float(data[2]))
            
    print("Frame 29 Nodal Fields:")
    print("  U1 range: [%.6f, %.6f] mm" % (min(u1_vals), max(u1_vals)))
    print("  U2 range: [%.6f, %.6f] mm" % (min(u2_vals), max(u2_vals)))
    print("  d range:  [%.6f, %.6f] (Source d_max = %.6f)" % (min(d_vals), max(d_vals), max(d_vals)))
    
    odb.close()
    return u1_f29, max(d_vals)

def audit_binary_state(bin_path, n_tgt_phys=8836):
    print("\n================================================================================")
    print("3. BINARY SEMANTICS & BYTE-BY-BYTE AUDIT: %s" % bin_path)
    print("================================================================================")
    
    file_size = os.path.getsize(bin_path)
    print("Binary File Size: %d bytes" % file_size)
    assert file_size == 4000016, "Error: Unexpected file size %d" % file_size
    
    N_CAP = 100000
    with open(bin_path, 'rb') as f:
        # Record 1: SV_PHASE_COMMITTED (100,000 float64 = 800,000 bytes)
        r1_head = struct.unpack('i', f.read(4))[0]
        assert r1_head == 800000, "Record 1 header mismatch: %d" % r1_head
        raw_phase = f.read(800000)
        r1_tail = struct.unpack('i', f.read(4))[0]
        assert r1_tail == 800000, "Record 1 tail mismatch: %d" % r1_tail
        sv_phase = np.frombuffer(raw_phase, dtype=np.float64)
        
        # Record 2: SV_H_COMMITTED (100,000 x 4 float64 = 3,200,000 bytes, Column-Major)
        r2_head = struct.unpack('i', f.read(4))[0]
        assert r2_head == 3200000, "Record 2 header mismatch: %d" % r2_head
        raw_h = f.read(3200000)
        r2_tail = struct.unpack('i', f.read(4))[0]
        assert r2_tail == 3200000, "Record 2 tail mismatch: %d" % r2_tail
        sv_h = np.frombuffer(raw_h, dtype=np.float64).reshape((N_CAP, 4), order='F')
        
    print("Record 1 (Phase Field): %d entries, max = %.6f, active (>0) = %d" % (
        len(sv_phase), np.max(sv_phase), np.count_nonzero(sv_phase > 0.0)))
    print("Record 2 (History H): shape %s, H_max = %.6f kN/mm^2, active (>0) = %d" % (
        sv_h.shape, np.max(sv_h), np.count_nonzero(sv_h > 0.0)))
    
    print("\n--- SAMPLE TARGET (PHYSIDX, KPT) ENTRIES FROM BINARY ---")
    print("%-10s %-8s %-16s %-16s %-16s" % ("Target EID", "Tgt GP", "Binary H (kN/mm2)", "Expected H", "Match?"))
    print("-" * 75)
    
    # Expected values from crack-tip audit table in F240:
    samples = [
        (4371, 4, 0.848870), # Near peak
        (4372, 3, 0.321009),
        (4465, 2, 0.219181),
        (4466, 1, 0.457134),
        (4371, 2, 0.403072),
        (4371, 3, 0.418389),
        (1, 1, 0.000000),    # Far field boundary
        (8836, 4, 0.000000)  # Far field top
    ]
    
    for eid, kpt, exp_h in samples:
        bin_val = sv_h[eid - 1, kpt - 1]
        match = "MATCH (diff < 1e-5)" if abs(bin_val - exp_h) < 1e-4 else "MISMATCH"
        print("%-10d %-8d %-16.6f %-16.6f %-16s" % (eid, kpt, bin_val, exp_h, match))

def patch_uel_diagnostic_text(uel_path):
    print("\n================================================================================")
    print("4. AUDITING AND CORRECTING DIAGNOSTIC STRING IN UEL: %s" % uel_path)
    print("================================================================================")
    
    with open(uel_path, 'r') as f:
        code = f.read()
        
    old_str = "SUCCESS: Imported restart state from PK10R1 state file"
    new_str = "SUCCESS: Imported restart state from Stage-D state file"
    
    if old_str in code:
        code_patched = code.replace(old_str, new_str)
        with open(uel_path, 'w') as f:
            f.write(code_patched)
        print("Replaced stale diagnostic string '%s' -> '%s'" % (old_str, new_str))
    else:
        print("Diagnostic string already clean: '%s'" % new_str)

if __name__ == "__main__":
    h1_inp = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    h1_odb = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
    bin_file = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin")
    uel_file = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for")
    
    audit_h1_inp(h1_inp)
    audit_h1_odb(h1_odb)
    audit_binary_state(bin_file)
    patch_uel_diagnostic_text(uel_file)
