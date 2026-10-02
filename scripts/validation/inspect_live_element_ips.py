# -*- coding: utf-8 -*-
"""
Inspect integration-point multiplicity and metadata for Layer 3 (All_elem) elements.
Audits:
- Element label
- Number of integration point values returned
- Position metadata (INTEGRATION_POINT, CENTROID, etc.)
- All SDV17, SDV18, SDV19, SDV20 values across all integration points of each inspected element
- Computes whether values across integration points are identical, averaged, or point-specific
- Compares global ODB sum under (1) Single representative value per element (deduplicated), and (2) Naive raw sum over all IP values
"""
from __future__ import print_function
import sys
import os
import json
from odbAccess import openOdb

def inspect_odb_ips(odb_path, sample_elements=None):
    print("=" * 80)
    print("INSPECTING ODB: %s" % odb_path)
    print("=" * 80)
    odb = openOdb(odb_path, readOnly=True)
    
    first_step = odb.steps.values()[0]
    last_frame = first_step.frames[-1]
    print("[INFO] Auditing Step '%s', Frame %d (Time = %.6f)" % (
        first_step.name, last_frame.frameId, last_frame.frameValue))
        
    fkeys = last_frame.fieldOutputs.keys()
    print("[INFO] Available Field Outputs: %s" % str(fkeys))
    
    # Check SDV field
    sdv_field = None
    if 'SDV' in fkeys:
        sdv_field = last_frame.fieldOutputs['SDV']
    elif 'SDV17' in fkeys:
        sdv_field = last_frame.fieldOutputs['SDV17']
        
    if sdv_field is None:
        print("[ERROR] No SDV field output found in frame.")
        odb.close()
        return
        
    print("[INFO] SDV Field Name: %s" % sdv_field.name)
    print("[INFO] Field Position: %s" % str(sdv_field.locations[0].position))
    print("[INFO] Total Field Value Records: %d" % len(sdv_field.values))
    
    # Collect data by element label
    elem_ip_map = {}
    for val in sdv_field.values:
        el = val.elementLabel
        ip = val.integrationPoint
        pos = val.position
        data = list(val.data) if hasattr(val.data, '__iter__') else [float(val.data)]
        if el not in elem_ip_map:
            elem_ip_map[el] = {}
        elem_ip_map[el][ip] = {
            'data': data,
            'position': str(pos)
        }
        
    all_elems = sorted(elem_ip_map.keys())
    print("[INFO] Unique Elements in Field Output: %d" % len(all_elems))
    print("[INFO] Element Label Range: %d .. %d" % (all_elems[0], all_elems[-1]))
    
    # Select sample elements
    if sample_elements is None:
        sample_elements = [all_elems[0], all_elems[1], all_elems[len(all_elems)//4], 
                           all_elems[len(all_elems)//2], all_elems[3*len(all_elems)//4], all_elems[-1]]
                           
    print("\n" + "=" * 80)
    print("DETAILED ELEMENT INTEGRATION-POINT AUDIT TABLE")
    print("=" * 80)
    print("%-10s | %-6s | %-18s | %-14s | %-14s | %-14s | %-14s | %-10s" % (
        "Element", "IP", "Position", "SDV17 (E_frac)", "SDV18 (E_elas)", "SDV19 (psi_f)", "SDV20 (psi_e)", "Identical?"))
    print("-" * 115)
    
    for el in sample_elements:
        if el not in elem_ip_map:
            continue
        ips = sorted(elem_ip_map[el].keys())
        num_ips = len(ips)
        
        # Check if all IPs have identical values
        sdv17_vals = []
        sdv18_vals = []
        sdv19_vals = []
        sdv20_vals = []
        
        for ip in ips:
            d = elem_ip_map[el][ip]['data']
            v17 = d[16] if len(d) >= 18 else (d[0] if len(d) == 1 else 0.0)
            v18 = d[17] if len(d) >= 18 else 0.0
            v19 = d[18] if len(d) >= 20 else 0.0
            v20 = d[19] if len(d) >= 20 else 0.0
            sdv17_vals.append(v17)
            sdv18_vals.append(v18)
            sdv19_vals.append(v19)
            sdv20_vals.append(v20)
            
        all_identical_17 = all(abs(v - sdv17_vals[0]) < 1e-18 for v in sdv17_vals)
        all_identical_18 = all(abs(v - sdv18_vals[0]) < 1e-18 for v in sdv18_vals)
        identical_str = "YES (4x dup)" if (all_identical_17 and all_identical_18) else "NO (differ)"
        
        for idx, ip in enumerate(ips):
            d = elem_ip_map[el][ip]['data']
            v17 = sdv17_vals[idx]
            v18 = sdv18_vals[idx]
            v19 = sdv19_vals[idx]
            v20 = sdv20_vals[idx]
            pos_str = elem_ip_map[el][ip]['position']
            print("%-10d | %-6d | %-18s | %-14.8e | %-14.8e | %-14.8e | %-14.8e | %-10s" % (
                el, ip, pos_str, v17, v18, v19, v20, identical_str if idx == 0 else ""))
        print("-" * 115)
        
    # Reduction comparison
    print("\n" + "=" * 80)
    print("GLOBAL REDUCTION COMPARISON (DEDUPLICATED VS NAIVE ALL-IP SUM)")
    print("=" * 80)
    
    # 1. Deduplicated sum (1 value per element, IP 1)
    dedup_e_frac = 0.0
    dedup_e_elas = 0.0
    for el in all_elems:
        ip1_data = elem_ip_map[el].get(1, list(elem_ip_map[el].values())[0])['data']
        v17 = ip1_data[16] if len(ip1_data) >= 18 else (ip1_data[0] if len(ip1_data) == 1 else 0.0)
        v18 = ip1_data[17] if len(ip1_data) >= 18 else 0.0
        dedup_e_frac += v17
        dedup_e_elas += v18
        
    # 2. Naive sum over all field value records
    naive_e_frac = 0.0
    naive_e_elas = 0.0
    for el in all_elems:
        for ip in elem_ip_map[el]:
            d = elem_ip_map[el][ip]['data']
            v17 = d[16] if len(d) >= 18 else (d[0] if len(d) == 1 else 0.0)
            v18 = d[17] if len(d) >= 18 else 0.0
            naive_e_frac += v17
            naive_e_elas += v18
            
    # RP work
    rp_u = 0.0
    rp_rf = 0.0
    if 'N_RP' in odb.rootAssembly.nodeSets:
        rp_set = odb.rootAssembly.nodeSets['N_RP']
        if 'U' in last_frame.fieldOutputs:
            u_sub = last_frame.fieldOutputs['U'].getSubset(region=rp_set)
            if len(u_sub.values) > 0:
                rp_u = float(u_sub.values[0].data[1])
        if 'RF' in last_frame.fieldOutputs:
            rf_sub = last_frame.fieldOutputs['RF'].getSubset(region=rp_set)
            if len(rf_sub.values) > 0:
                rp_rf = float(rf_sub.values[0].data[1])
    w_ext_lin = 0.5 * rp_rf * rp_u
    
    print("1. DEDUPLICATED REDUCTION (1 Value per Element / Single IP):")
    print("   - E_elas (Global Sum): %.8e kN*mm (%.8f mJ)" % (dedup_e_elas, dedup_e_elas * 1000.0))
    print("   - E_frac (Global Sum): %.8e kN*mm (%.8f mJ)" % (dedup_e_frac, dedup_e_frac * 1000.0))
    print("   - E_model Total:       %.8e kN*mm (%.8f mJ)" % (dedup_e_elas + dedup_e_frac, (dedup_e_elas + dedup_e_frac) * 1000.0))
    print("   - RP External Work:    %.8e kN*mm (%.8f mJ)" % (w_ext_lin, w_ext_lin * 1000.0))
    print("   - Bookkeeping Delta:   %+.8e kN*mm (%+.6f mJ)" % (
        (dedup_e_elas + dedup_e_frac) - w_ext_lin, ((dedup_e_elas + dedup_e_frac) - w_ext_lin) * 1000.0))
    print("   - Relative Residual:   %+.4f %%" % (
        (((dedup_e_elas + dedup_e_frac) - w_ext_lin) / max(w_ext_lin, 1e-15)) * 100.0))
        
    print("\n2. NAIVE ALL-INTEGRATION-POINTS SUM (Without Deduplication):")
    print("   - E_elas (Naive Sum):  %.8e kN*mm (%.8f mJ)" % (naive_e_elas, naive_e_elas * 1000.0))
    print("   - E_frac (Naive Sum):  %.8e kN*mm (%.8f mJ)" % (naive_e_frac, naive_e_frac * 1000.0))
    print("   - E_model Total:       %.8e kN*mm (%.8f mJ)" % (naive_e_elas + naive_e_frac, (naive_e_elas + naive_e_frac) * 1000.0))
    print("   - Multiplicity Ratio:  %.4f x (Exactly 4x for 4-IP CPE4 elements)" % (
        (naive_e_elas + naive_e_frac) / max(dedup_e_elas + dedup_e_frac, 1e-15)))
    print("   - Naive Residual:      %+.4f %% (Overcounting by ~300%%!)" % (
        (((naive_e_elas + naive_e_frac) - w_ext_lin) / max(w_ext_lin, 1e-15)) * 100.0))
        
    odb.close()

if __name__ == '__main__':
    odb_p = sys.argv[1] if len(sys.argv) > 1 else 'PK_M1_REF15K_ENERGY.odb'
    inspect_odb_ips(odb_p)
