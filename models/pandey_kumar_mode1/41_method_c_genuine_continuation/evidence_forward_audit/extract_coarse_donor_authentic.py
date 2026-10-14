# -*- coding: utf-8 -*-
"""
extract_coarse_donor_authentic.py
Extracts authentic field state from M1_PRE_1S.odb at u = 0.0050 mm (Increment 500).
Extracts:
- Element damage SDV14 across all 2,906 elements
- Element history H from SDV2 across all 2,906 elements (4 GPs per quad, 1 per tri)
- Element energies (SDV17: E_frac, SDV18: E_elas)
- Node coordinates and connectivity from inst
- Nodal damage d by topological element-to-node averaging
- RP reaction force and displacement
Outputs: coarse_donor_state_u0050.json
"""
import sys
import os
import json
import odbAccess

def extract():
    odb_path = '/scratch9/pr21vyci/runs/mode1_method_b_f1408/01_pre_1s/M1_PRE_1S.odb'
    out_json = '/scratch9/pr21vyci/runs/mode1_method_b_f1408/01_pre_1s/coarse_donor_state_u0050.json'

    print("[INFO] Opening ODB: %s" % odb_path)
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly
    inst = root.instances['PART-1-1']

    step = odb.steps['Step-1']
    last_frame = step.frames[-1]
    fkeys = last_frame.fieldOutputs.keys()

    # 1. Element damage SDV14 (at integration points)
    # UMAT elements are labeled 5813..8718
    # Map to base physical element: phys_eid = eid - 5812
    elem_d_ips = {}
    if 'SDV14' in fkeys:
        for val in last_frame.fieldOutputs['SDV14'].values:
            eid = val.elementLabel
            if eid > 5812:
                phys_eid = eid - 5812
            elif eid > 2906:
                phys_eid = eid - 2906
            else:
                phys_eid = eid
            if phys_eid not in elem_d_ips:
                elem_d_ips[phys_eid] = []
            elem_d_ips[phys_eid].append(float(val.data))

    elem_d = {eid: sum(vals)/float(len(vals)) for eid, vals in elem_d_ips.items()}

    # 2. History field H from SDV2 (at integration points)
    elem_h_ips = {}
    if 'SDV2' in fkeys:
        for val in last_frame.fieldOutputs['SDV2'].values:
            eid = val.elementLabel
            if eid > 5812:
                phys_eid = eid - 5812
            elif eid > 2906:
                phys_eid = eid - 2906
            else:
                phys_eid = eid
            if phys_eid not in elem_h_ips:
                elem_h_ips[phys_eid] = []
            elem_h_ips[phys_eid].append(float(val.data))

    # 3. Element energies SDV17 (E_frac), SDV18 (E_elas)
    e_frac_elem = {}
    if 'SDV17' in fkeys:
        for val in last_frame.fieldOutputs['SDV17'].values:
            eid = val.elementLabel
            phys_eid = eid - 5812 if eid > 5812 else (eid - 2906 if eid > 2906 else eid)
            e_frac_elem[phys_eid] = float(val.data)

    e_elas_elem = {}
    if 'SDV18' in fkeys:
        for val in last_frame.fieldOutputs['SDV18'].values:
            eid = val.elementLabel
            phys_eid = eid - 5812 if eid > 5812 else (eid - 2906 if eid > 2906 else eid)
            e_elas_elem[phys_eid] = float(val.data)

    # 4. Reaction force at RP
    rf_rp_n = 0.0
    u_rp_mm = 0.0050
    if 'RF' in fkeys:
        for val in last_frame.fieldOutputs['RF'].values:
            if val.nodeLabel == 999999:
                rf_rp_n = float(val.data[1]) * 1000.0

    if 'U' in fkeys:
        for val in last_frame.fieldOutputs['U'].values:
            if val.nodeLabel == 999999:
                u_rp_mm = float(val.data[1])

    # 5. Node coordinates and element connectivity from instance
    node_coords = {}
    for node in inst.nodes:
        node_coords[node.label] = [float(node.coordinates[0]), float(node.coordinates[1])]

    elem_conn = {}
    for elem in inst.elements:
        if elem.label <= 2906:
            elem_conn[elem.label] = list(elem.connectivity)

    # Compute nodal damage by element-to-node averaging
    node_d = {}
    node_count = {}
    for eid, conn in elem_conn.items():
        d_val = elem_d.get(eid, 0.0)
        for nid in conn:
            node_d[nid] = node_d.get(nid, 0.0) + d_val
            node_count[nid] = node_count.get(nid, 0) + 1

    d_nodal = {nid: node_d[nid] / float(node_count[nid]) for nid in node_d}

    max_d_nodal = max(d_nodal.values()) if d_nodal else 0.0
    max_d_elem = max(elem_d.values()) if elem_d else 0.0
    min_h = min([min(hl) for hl in elem_h_ips.values()]) if elem_h_ips else 0.0
    max_h = max([max(hl) for hl in elem_h_ips.values()]) if elem_h_ips else 0.0

    print("[INFO] Extracted %d element damages (max = %.6f)" % (len(elem_d), max_d_elem))
    print("[INFO] Extracted %d nodal damages (max = %.6f)" % (len(d_nodal), max_d_nodal))
    print("[INFO] Extracted %d element history lists (min = %.6e, max = %.6e)" % (len(elem_h_ips), min_h, max_h))
    print("[INFO] RP reaction force: %.4f N, RP displacement: %.6f mm" % (rf_rp_n, u_rp_mm))

    total_e_frac = sum(e_frac_elem.values())
    total_e_elas = sum(e_elas_elem.values())
    print("[INFO] Total E_frac: %.6e kN*mm (%.4f mJ)" % (total_e_frac, total_e_frac * 1000.0))
    print("[INFO] Total E_elas: %.6e kN*mm (%.4f mJ)" % (total_e_elas, total_e_elas * 1000.0))

    result = {
        "job_name": "M1_PRE_1S",
        "u_rp_mm": u_rp_mm,
        "rf_rp_N": rf_rp_n,
        "total_e_frac_mJ": total_e_frac * 1000.0,
        "total_e_elas_mJ": total_e_elas * 1000.0,
        "total_e_tot_mJ": (total_e_frac + total_e_elas) * 1000.0,
        "max_d_elem": max_d_elem,
        "max_d_nodal": max_d_nodal,
        "min_H": min_h,
        "max_H": max_h,
        "num_elements": len(elem_d),
        "num_nodes": len(d_nodal),
        "d_elem": {str(k): v for k, v in elem_d.items()},
        "d_nodal": {str(k): v for k, v in d_nodal.items()},
        "h_gp": {str(k): v for k, v in elem_h_ips.items()},
        "e_frac_elem": {str(k): v for k, v in e_frac_elem.items()},
        "e_elas_elem": {str(k): v for k, v in e_elas_elem.items()}
    }

    with open(out_json, 'w') as f:
        json.dump(result, f)

    print("[INFO] Saved complete coarse donor state JSON (size %d bytes)" % os.path.getsize(out_json))
    odb.close()

if __name__ == '__main__':
    extract()
