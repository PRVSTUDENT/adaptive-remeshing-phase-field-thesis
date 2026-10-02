#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct source-deck parsing of INP, UEL Fortran, and STAGE_D_COMMITTED_STATE.bin
to reconstruct exact physical mesh layers, element sizes, material parameters, and 4-GP history.
"""

import os
import sys
import struct
import math
import json

def parse_inp_file(inp_path):
    print("Parsing INP: %s" % inp_path)
    nodes = {}
    elements = {} # elem_id -> (elem_type, [nodes])
    element_sets = {} # set_name -> [elem_ids]
    uel_properties = []
    
    current_section = None
    current_set_name = None
    current_elem_type = None
    
    with open(inp_path, 'r') as fp:
        lines = fp.readlines()
        
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        if line.startswith('*'):
            parts = [p.strip() for p in line.split(',')]
            keyword = parts[0].upper()
            
            if keyword == '*NODE':
                current_section = 'NODE'
            elif keyword == '*ELEMENT':
                current_section = 'ELEMENT'
                current_elem_type = 'UNKNOWN'
                current_set_name = None
                for p in parts[1:]:
                    if p.upper().startswith('TYPE='):
                        current_elem_type = p.split('=')[1].strip()
                    elif p.upper().startswith('ELSET='):
                        current_set_name = p.split('=')[1].strip()
                if current_set_name and current_set_name not in element_sets:
                    element_sets[current_set_name] = []
            elif keyword == '*UEL PROPERTY':
                current_section = 'UEL_PROP'
                # next lines contain numbers
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('*'):
                    for val in lines[i].strip().split(','):
                        val_str = val.strip()
                        if val_str:
                            try:
                                uel_properties.append(float(val_str))
                            except ValueError:
                                pass
                    i += 1
                continue
            elif keyword.startswith('*ELSET'):
                current_section = 'ELSET'
                current_set_name = None
                for p in parts[1:]:
                    if p.upper().startswith('ELSET='):
                        current_set_name = p.split('=')[1].strip()
                if current_set_name and current_set_name not in element_sets:
                    element_sets[current_set_name] = []
            else:
                current_section = 'OTHER'
            i += 1
            continue
            
        # Data lines
        if current_section == 'NODE':
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3]) if len(parts) > 3 else 0.0
                    nodes[nid] = (x, y, z)
                except ValueError:
                    pass
        elif current_section == 'ELEMENT':
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                try:
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:] if p.isdigit()]
                    elements[eid] = (current_elem_type, nids)
                    if current_set_name:
                        element_sets[current_set_name].append(eid)
                except ValueError:
                    pass
        elif current_section == 'ELSET':
            parts = [p.strip() for p in line.split(',')]
            for p in parts:
                if p.isdigit() and current_set_name:
                    element_sets[current_set_name].append(int(p))
                    
        i += 1
        
    return nodes, elements, element_sets, uel_properties

def analyze_mesh_facts(name, nodes, elements, element_sets, uel_properties):
    print("\n================================================================================")
    print("SOURCE-DECK MESH & MATERIAL AUDIT: %s" % name)
    print("================================================================================")
    
    # 1. Classify Element Types / Layers
    type_counts = {}
    for eid, (etype, nids) in elements.items():
        type_counts[etype] = type_counts.get(etype, 0) + 1
        
    print("1. Element Classification by Type / Layer:")
    for etype, cnt in sorted(type_counts.items()):
        print("   Type %-20s: %d elements" % (etype, cnt))
        
    # In Abaqus phase field models, there are often stacked elements on the SAME nodes:
    # e.g., UEL user element for phase field / coupled field + CPS4/CPS4R for visualization or standard Abaqus mesh
    # Let's count unique quad node-topologies (physical quads)
    unique_quads = set()
    for eid, (etype, nids) in elements.items():
        if len(nids) == 4:
            # canonical quad representation
            sorted_nids = tuple(sorted(nids))
            unique_quads.add(sorted_nids)
            
    # RP node
    non_rp_nodes = {nid: (x, y) for nid, (x, y, z) in nodes.items() if abs(x) <= 1.0 and abs(y) <= 1.0}
    
    print("\n2. Physical Mesh Facts (Direct Geometry):")
    print("   Total Physical Nodes:   %d (Excluding RP)" % len(non_rp_nodes))
    print("   Total Physical Quads:   %d (Unique geometric 4-node cells)" % len(unique_quads))
    print("   Total Deck Elements:    %d (Stacked layers: phase UEL + mech/vis)" % len(elements))
    
    # 2. Compute Physical Element Sizes h (edge lengths) for unique quads
    h_values = []
    aspect_ratios = []
    process_zone_h = [] # for quads near notch (x in [-0.1, 0.1], y in [-0.1, 0.1])
    ligament_h = [] # for quads along uncracked ligament (x in [0, 0.5], y in [-0.05, 0.05])
    
    quad_centers_and_sizes = []
    
    for quad in unique_quads:
        # quad has 4 node IDs
        coords = [non_rp_nodes[nid] for nid in quad if nid in non_rp_nodes]
        if len(coords) == 4:
            cx = sum(c[0] for c in coords) / 4.0
            cy = sum(c[1] for c in coords) / 4.0
            # edge lengths
            d12 = math.sqrt((coords[0][0]-coords[1][0])**2 + (coords[0][1]-coords[1][1])**2)
            d23 = math.sqrt((coords[1][0]-coords[2][0])**2 + (coords[1][1]-coords[2][1])**2)
            d34 = math.sqrt((coords[2][0]-coords[3][0])**2 + (coords[2][1]-coords[3][1])**2)
            d41 = math.sqrt((coords[3][0]-coords[0][0])**2 + (coords[3][1]-coords[0][1])**2)
            
            edges = [d12, d23, d34, d41]
            h_min_e = min(edges)
            h_max_e = max(edges)
            h_avg_e = sum(edges) / 4.0
            ar_e = h_max_e / h_min_e if h_min_e > 1e-12 else 1.0
            
            h_values.append(h_avg_e)
            aspect_ratios.append(ar_e)
            quad_centers_and_sizes.append((cx, cy, h_avg_e, ar_e))
            
            if abs(cx) <= 0.10 and abs(cy) <= 0.10:
                process_zone_h.append(h_avg_e)
            if 0.0 <= cx <= 0.50 and abs(cy) <= 0.05:
                ligament_h.append(h_avg_e)
                
    print("\n3. Physical Element Size Distribution (Edge Length h):")
    print("   Global h_min:          %.6f mm" % min(h_values))
    print("   Global h_max:          %.6f mm" % max(h_values))
    print("   Global Mean h:         %.6f mm" % (sum(h_values)/len(h_values)))
    print("   Process Zone h (mean): %.6f mm (min: %.6f, max: %.6f)" % (
        sum(process_zone_h)/len(process_zone_h), min(process_zone_h), max(process_zone_h)))
    print("   Ligament h (mean):     %.6f mm (min: %.6f, max: %.6f)" % (
        sum(ligament_h)/len(ligament_h), min(ligament_h), max(ligament_h)))
    print("   Max Aspect Ratio:      %.4f (Mean: %.4f)" % (max(aspect_ratios), sum(aspect_ratios)/len(aspect_ratios)))
    
    # 3. Material Properties from UEL Property Array
    print("\n4. Material Parameters Read from Deck / UEL Properties:")
    print("   UEL Properties Array Length: %d" % len(uel_properties))
    print("   Raw Properties: %s" % uel_properties)
    # Common UEL layout: E, nu, Gc, l0, k, etc.
    if len(uel_properties) >= 4:
        print("   -> Young's Modulus E:       %.2e MPa / N/mm^2" % uel_properties[0])
        print("   -> Poisson's Ratio nu:      %.4f" % uel_properties[1])
        print("   -> Fracture Toughness Gc:   %.6e N/mm (kJ/m^2)" % uel_properties[2])
        print("   -> Phase Field Length l0:   %.6f mm" % uel_properties[3])
        if len(uel_properties) >= 5:
            print("   -> Residual Stiffness k:    %.6e" % uel_properties[4])
        l0 = uel_properties[3]
        h_pz = sum(process_zone_h)/len(process_zone_h)
        print("   -> Discretization Ratio h/l0 in Process Zone: %.4f (h = %.4f mm, l0 = %.4f mm)" % (
            h_pz / l0, h_pz, l0))
            
    return quad_centers_and_sizes

def audit_committed_state_bin(bin_path):
    print("\n================================================================================")
    print("COMMITTED STATE BINARY AUDIT: %s" % bin_path)
    print("================================================================================")
    if not os.path.exists(bin_path):
        print("ERROR: File not found: %s" % bin_path)
        return
        
    file_size = os.path.getsize(bin_path)
    print("File Size: %d bytes" % file_size)
    
    # STAGE_D_COMMITTED_STATE.bin format:
    # Let's inspect how many double/float values it contains:
    # 6,400,016 bytes: 6400016 / 8 = 800,002 double precision numbers (or header + arrays)
    with open(bin_path, 'rb') as fp:
        raw_header = fp.read(64)
        
    # Read first few floats/doubles/ints
    print("First 32 bytes hex: %s" % raw_header[:32].hex())
    
    # Let's check if it has integer counts in first 16 bytes:
    ints = struct.unpack('<8i', raw_header[:32])
    print("First 8 integers: %s" % list(ints))
    doubles = struct.unpack('<4d', raw_header[:32])
    print("First 4 doubles: %s" % list(doubles))

def main():
    ctrl_inp = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.inp"
    trans_inp = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp"
    bin_file = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin"
    
    n_ctrl, e_ctrl, s_ctrl, p_ctrl = parse_inp_file(ctrl_inp)
    analyze_mesh_facts("Native Bounded Control (1390278)", n_ctrl, e_ctrl, s_ctrl, p_ctrl)
    
    n_trans, e_trans, s_trans, p_trans = parse_inp_file(trans_inp)
    analyze_mesh_facts("Stage-D Nonmatching Transfer (1390279)", n_trans, e_trans, s_trans, p_trans)
    
    audit_committed_state_bin(bin_file)

if __name__ == "__main__":
    main()
