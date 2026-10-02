#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic Provenance Audit across Exact Jobs:
1390447.mmaster02 — Historical Stage-D donor continuous control
1390552.mmaster02 — I_A=12 donor isolation qualification
1390876.mmaster02 — dt_min=1e-11 donor isolation qualification
"""

import os
import sys
import hashlib
import json
import re

def sha256_bytes(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def sha256_file(filepath):
    if not os.path.exists(filepath):
        return "MISSING"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def analyze_deck(inp_path, for_path, pbs_path):
    with open(inp_path, "rb") as f:
        inp_content = f.read()
    inp_text = inp_content.decode('utf-8', errors='ignore')
    
    # 1. Parse Nodes
    node_lines = []
    in_node = False
    for line in inp_text.splitlines():
        line_s = line.strip()
        if line_s.upper().startswith("*NODE"):
            in_node = True
            continue
        if in_node:
            if line_s.startswith("*"):
                in_node = False
            elif line_s:
                node_lines.append(line_s)
                
    # Check node labels
    node_ids = []
    rp_found = False
    rp_label = None
    for nl in node_lines:
        parts = nl.split(",")
        try:
            nid = int(parts[0].strip())
            if nid == 99999 or "RP" in nl.upper():
                rp_found = True
                rp_label = nid
            else:
                node_ids.append(nid)
        except ValueError:
            pass
            
    # Check physical elements and UEL elements
    in_elem = False
    elem_type = None
    quad_elems = []
    uel_elems = []
    phase_uel_count = 0
    mech_uel_count = 0
    
    for line in inp_text.splitlines():
        line_s = line.strip()
        if line_s.upper().startswith("*ELEMENT"):
            in_elem = True
            m_type = re.search(r"TYPE=([A-Za-z0-9]+)", line_s, re.IGNORECASE)
            elem_type = m_type.group(1) if m_type else "UNKNOWN"
            continue
        if in_elem:
            if line_s.startswith("*"):
                in_elem = False
            elif line_s:
                parts = line_s.split(",")
                try:
                    eid = int(parts[0].strip())
                    if elem_type.upper().startswith("U"):
                        uel_elems.append((eid, elem_type))
                        if "U1" in elem_type.upper() or elem_type.upper() == "U1":
                            phase_uel_count += 1
                        else:
                            mech_uel_count += 1
                    else:
                        quad_elems.append((eid, elem_type))
                except ValueError:
                    pass
                    
    # PROPS
    props_values = []
    for idx, line in enumerate(inp_text.splitlines()):
        if line.strip().upper().startswith("*UEL PROPERTY"):
            next_line = inp_text.splitlines()[idx+1]
            props_values = [p.strip() for p in next_line.split(",")]
            break
            
    props_6 = props_values[5] if len(props_values) > 5 else "N/A"
    props_7 = props_values[6] if len(props_values) > 6 else "N/A"
    
    # Controls and Static
    static_line = ""
    controls_line = ""
    for idx, line in enumerate(inp_text.splitlines()):
        if line.strip().upper().startswith("*STATIC"):
            static_line = inp_text.splitlines()[idx+1].strip()
        if line.strip().upper().startswith("*CONTROLS, PARAMETERS=TIME INCREMENTATION"):
            controls_line = inp_text.splitlines()[idx+1].strip()
            
    # Node coordinates hash
    coord_hash = sha256_bytes("\n".join(node_lines).encode('utf-8'))
    
    return {
        "inp_path": inp_path,
        "inp_sha256": sha256_file(inp_path),
        "for_sha256": sha256_file(for_path),
        "pbs_sha256": sha256_file(pbs_path),
        "physical_nodes_excl_rp": len(node_ids),
        "min_node_id": min(node_ids) if node_ids else 0,
        "max_node_id": max(node_ids) if node_ids else 0,
        "rp_node_label": rp_label,
        "physical_quad_count": len(quad_elems),
        "total_uel_count": len(uel_elems),
        "phase_uel_count": len(uel_elems),
        "mech_uel_count": 0,
        "coord_hash": coord_hash,
        "props_6": props_6,
        "props_7": props_7,
        "static_line": static_line,
        "controls_line": controls_line
    }

def main():
    # 1. 1390447
    deck_447_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    inp_447 = os.path.join(deck_447_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp")
    for_447 = os.path.join(deck_447_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_447 = os.path.join(deck_447_dir, "submit_job.pbs")
    
    # 2. 1390552
    deck_552_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL"
    inp_552 = os.path.join(deck_552_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.inp")
    for_552 = os.path.join(deck_552_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_552 = os.path.join(deck_552_dir, "submit_job.pbs")
    
    # 3. 1390876
    deck_876_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL"
    inp_876 = os.path.join(deck_876_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    for_876 = os.path.join(deck_876_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_876 = os.path.join(deck_876_dir, "submit_job.pbs")
    
    print("================================================================================")
    print("DETERMINISTIC PROVENANCE AUDIT: 1390447 vs 1390552 vs 1390876")
    print("================================================================================")
    res_447 = analyze_deck(inp_447, for_447, pbs_447)
    res_552 = analyze_deck(inp_552, for_552, pbs_552)
    res_876 = analyze_deck(inp_876, for_876, pbs_876)
    
    for name, r in [("Job 1390447 (Historical Donor Control)", res_447),
                    ("Job 1390552 (I_A=12 Isolation)", res_552),
                    ("Job 1390876 (dt_min=1e-11 Isolation)", res_876)]:
        print("\n--------------------------------------------------------------------------------")
        print("JOB: %s" % name)
        print("--------------------------------------------------------------------------------")
        print("  Exact Package Path : %s" % os.path.dirname(r["inp_path"]))
        print("  .inp SHA-256       : %s" % r["inp_sha256"])
        print("  UEL .for SHA-256   : %s" % r["for_sha256"])
        print("  Physical Nodes     : %d (IDs: %d .. %d)" % (r["physical_nodes_excl_rp"], r["min_node_id"], r["max_node_id"]))
        print("  RP Node Label      : %s" % r["rp_node_label"])
        print("  Physical Quads     : %d" % r["physical_quad_count"])
        print("  Total UEL Elements : %d" % r["total_uel_count"])
        print("  Nodal Coord SHA-256: %s" % r["coord_hash"])
        print("  PROPS(6), PROPS(7) : %s, %s" % (r["props_6"], r["props_7"]))
        print("  *STATIC Line       : %s" % r["static_line"])
        print("  *CONTROLS Line     : %s" % (r["controls_line"] if r["controls_line"] else "Omitted (Abaqus Defaults)"))
        
    audit_data = {
        "job_1390447": res_447,
        "job_1390552": res_552,
        "job_1390876": res_876,
        "node_counts_identical": (res_447["physical_nodes_excl_rp"] == res_552["physical_nodes_excl_rp"] == res_876["physical_nodes_excl_rp"]),
        "quad_counts_identical": (res_447["physical_quad_count"] == res_552["physical_quad_count"] == res_876["physical_quad_count"]),
        "uel_counts_identical": (res_447["total_uel_count"] == res_552["total_uel_count"] == res_876["total_uel_count"]),
        "coord_hash_identical": (res_447["coord_hash"] == res_552["coord_hash"] == res_876["coord_hash"])
    }
    with open("models/generated/mode_ii/stage_e_refinement_coarsening_batch/donor_provenance_audit.json", "w") as fp:
        json.dump(audit_data, fp, indent=2)
        
    print("\n================================================================================")
    print("LINEAGE PARITY SUMMARY:")
    print("  Node counts match across all 3: %s (%d nodes)" % (audit_data["node_counts_identical"], res_447["physical_nodes_excl_rp"]))
    print("  Quad counts match across all 3: %s (%d quads)" % (audit_data["quad_counts_identical"], res_447["physical_quad_count"]))
    print("  UEL counts match across all 3 : %s (%d UELs)" % (audit_data["uel_counts_identical"], res_447["total_uel_count"]))
    print("  Coord hash identical all 3    : %s" % audit_data["coord_hash_identical"])
    print("================================================================================")

if __name__ == "__main__":
    main()
