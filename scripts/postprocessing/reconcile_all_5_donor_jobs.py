#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canonical Donor Trajectory Extraction, Input Provenance, and Bit-for-Bit Parity Audit
across 1390447, 1390552, 1390876, 1391301, and 1391302
"""

import os
import sys
import hashlib
import json
import numpy as np
from odbAccess import openOdb

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def extract_canonical_odb(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    step_name = list(odb.steps.keys())[0]
    step = odb.steps[step_name]
    num_frames = len(step.frames)
    
    frames_data = []
    for f_idx, frame in enumerate(step.frames):
        rp_u1 = 0.0
        rp_rf1 = 0.0
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == 99999:
                    rp_u1 = float(v.data[0])
                    break
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == 99999:
                    rp_rf1 = float(v.data[0])
                    break
                    
        d_vals = []
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel != 99999 and len(v.data) >= 3:
                    d_vals.append(float(v.data[2]))
                    
        max_d = max(d_vals) if d_vals else 0.0
        min_d = min(d_vals) if d_vals else 0.0
        
        frames_data.append({
            "frame_idx": f_idx,
            "frame_value": float(frame.frameValue),
            "rp_u1_mm": rp_u1,
            "rp_rf1_kN": rp_rf1,
            "min_d": min_d,
            "max_d": max_d
        })
        
    odb.close()
    
    # Peak calculation
    peak_rf1 = -1e9
    peak_frame = None
    peak_u1 = None
    for f in frames_data:
        if f["rp_rf1_kN"] > peak_rf1:
            peak_rf1 = f["rp_rf1_kN"]
            peak_frame = f["frame_idx"]
            peak_u1 = f["rp_u1_mm"]
            
    # Handoff calculation (Frame 17)
    f17 = frames_data[17] if len(frames_data) > 17 else None
    flast = frames_data[-1]
    
    return {
        "step_name": step_name,
        "num_frames_including_0": num_frames,
        "num_increments": num_frames - 1,
        "rp_node": 99999,
        "rp_set": "N_RP",
        "rf_component": "RF1 (Positive in +X direction)",
        "terminal_u1_mm": flast["rp_u1_mm"],
        "terminal_rf1_kN": flast["rp_rf1_kN"],
        "terminal_d_max": flast["max_d"],
        "peak_rf1_kN": peak_rf1,
        "peak_frame": peak_frame,
        "peak_u1_mm": peak_u1,
        "handoff_frame": 17,
        "handoff_u1_mm": f17["rp_u1_mm"] if f17 else None,
        "handoff_rf1_kN": f17["rp_rf1_kN"] if f17 else None,
        "handoff_d_max": f17["max_d"] if f17 else None,
        "all_frames": frames_data
    }

def audit_input_deck(inp_path):
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    nodes = set()
    quads = set()
    uel_phase = set()
    props_lines = []
    static_cards = []
    controls_cards = []
    
    in_nodes = False
    in_quads = False
    in_uel_phase = False
    
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.startswith("*NODE"):
            in_nodes = True
            in_quads = False
            in_uel_phase = False
            continue
        elif line_s.startswith("*ELEMENT, TYPE=CPE4") or line_s.startswith("*ELEMENT, TYPE=U1"):
            in_nodes = False
            in_quads = True
            in_uel_phase = False
            continue
        elif line_s.startswith("*ELEMENT, TYPE=U2"):
            in_nodes = False
            in_quads = False
            in_uel_phase = True
            continue
        elif line_s.startswith("*"):
            in_nodes = False
            in_quads = False
            in_uel_phase = False
            
        if in_nodes and line_s and not line_s.startswith("**"):
            parts = line_s.split(",")
            try:
                nid = int(parts[0].strip())
                if nid != 99999:
                    nodes.add(nid)
            except: pass
            
        if in_quads and line_s and not line_s.startswith("**"):
            parts = line_s.split(",")
            try:
                eid = int(parts[0].strip())
                quads.add(eid)
            except: pass
            
        if in_uel_phase and line_s and not line_s.startswith("**"):
            parts = line_s.split(",")
            try:
                eid = int(parts[0].strip())
                uel_phase.add(eid)
            except: pass
            
        if "*UEL PROPERTY" in line_s:
            props_lines.append(lines[i+1].strip())
        if "*STATIC" in line_s:
            static_cards.append(lines[i+1].strip())
        if "*CONTROLS, PARAMETERS=TIME INCREMENTATION" in line_s:
            controls_cards.append(lines[i+1].strip())
            
    return {
        "physical_nodes_excl_rp": len(nodes),
        "physical_quads": len(quads),
        "phase_uels": len(uel_phase),
        "props": props_lines,
        "static_cards": static_cards,
        "controls_cards": controls_cards
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    jobs = [
        {
            "job_id": "1390447.mmaster02",
            "label": "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL (1390447)",
            "odb_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.odb"),
            "inp_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.inp"),
            "for_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/f44_mixed_uel_restart_stateinit.for")
        },
        {
            "job_id": "1390552.mmaster02",
            "label": "M2CORR_STAGE_E_DONOR_CONTROL_VAL (1390552)",
            "odb_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_CONTROL_VAL/M2CORR_STAGE_E_DONOR_CONTROL_VAL.odb"),
            "inp_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_CONTROL_VAL/M2CORR_STAGE_E_DONOR_CONTROL_VAL.inp"),
            "for_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_CONTROL_VAL/f44_mixed_uel_restart_stateinit.for")
        },
        {
            "job_id": "1390876.mmaster02",
            "label": "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL (1390876)",
            "odb_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.odb"),
            "inp_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.inp"),
            "for_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/f44_mixed_uel_restart_stateinit.for")
        },
        {
            "job_id": "1391301.mmaster02",
            "label": "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL (1391301)",
            "odb_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL.odb"),
            "inp_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL.inp"),
            "for_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/f44_mixed_uel_restart_stateinit.for")
        },
        {
            "job_id": "1391302.mmaster02",
            "label": "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL (1391302)",
            "odb_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL.odb"),
            "inp_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL.inp"),
            "for_path": os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/f44_mixed_uel_restart_stateinit.for")
        }
    ]
    
    extracted_data = {}
    
    print("================================================================================")
    print("CANONICAL EXTRACTION & PROVENANCE RECONCILIATION ACROSS ALL 5 DONOR JOBS:")
    print("================================================================================")
    
    for job in jobs:
        print("\nAUDITING: %s" % job["label"])
        odb_data = extract_canonical_odb(job["odb_path"])
        inp_data = audit_input_deck(job["inp_path"])
        inp_sha = sha256_file(job["inp_path"])
        for_sha = sha256_file(job["for_path"])
        
        print("  Step Name: %s | Total Frames: %d (Frames 0 to %d) | Total Increments: %d" % (
            odb_data["step_name"], odb_data["num_frames_including_0"],
            odb_data["num_frames_including_0"] - 1, odb_data["num_increments"]
        ))
        print("  Handoff Frame 17: U1 = %10.8f mm | RF1 = %10.8f kN | d_max = %10.8f" % (
            odb_data["handoff_u1_mm"], odb_data["handoff_rf1_kN"], odb_data["handoff_d_max"]
        ))
        print("  Peak Load Frame %d: U1 = %10.8f mm | RF1 = %10.8f kN" % (
            odb_data["peak_frame"], odb_data["peak_u1_mm"], odb_data["peak_rf1_kN"]
        ))
        print("  Terminal Frame %d: U1 = %10.8f mm | RF1 = %10.8f kN | d_max = %10.8f" % (
            odb_data["num_frames_including_0"] - 1, odb_data["terminal_u1_mm"],
            odb_data["terminal_rf1_kN"], odb_data["terminal_d_max"]
        ))
        print("  Mesh: %d nodes (excl RP 99999), %d quads (%d mech / %d phase UELs)" % (
            inp_data["physical_nodes_excl_rp"], inp_data["physical_quads"],
            inp_data["physical_quads"], inp_data["phase_uels"]
        ))
        print("  INP SHA256: %s" % inp_sha)
        print("  FOR SHA256: %s" % for_sha)
        print("  STATIC card:   %s" % inp_data["static_cards"])
        print("  CONTROLS card: %s" % inp_data["controls_cards"])
        
        extracted_data[job["job_id"]] = {
            "job_id": job["job_id"],
            "label": job["label"],
            "odb_data": odb_data,
            "inp_data": inp_data,
            "inp_sha256": inp_sha,
            "for_sha256": for_sha
        }
        
    # Bit-for-bit parity check against 1390876
    base_frames = extracted_data["1390876.mmaster02"]["odb_data"]["all_frames"]
    for jid in ["1390447.mmaster02", "1390552.mmaster02", "1391301.mmaster02", "1391302.mmaster02"]:
        comp_frames = extracted_data[jid]["odb_data"]["all_frames"]
        max_d_rf = max(abs(f1["rp_rf1_kN"] - f2["rp_rf1_kN"]) for f1, f2 in zip(base_frames, comp_frames))
        max_d_u = max(abs(f1["rp_u1_mm"] - f2["rp_u1_mm"]) for f1, f2 in zip(base_frames, comp_frames))
        max_d_d = max(abs(f1["max_d"] - f2["max_d"]) for f1, f2 in zip(base_frames, comp_frames))
        print("\nParity Check vs 1390876 for %s:" % jid)
        print("  Max Delta RF1: %12.5e kN | Max Delta U1: %12.5e mm | Max Delta d: %12.5e" % (
            max_d_rf, max_d_u, max_d_d
        ))
        
    # Save JSON summary without massive frame dumps
    json_summary = {}
    for jid, d in extracted_data.items():
        summary_d = dict(d)
        summary_odb = dict(d["odb_data"])
        del summary_odb["all_frames"]
        summary_d["odb_data"] = summary_odb
        json_summary[jid] = summary_d
        
    out_json = os.path.join(base_dir, "canonical_donor_lineage_reconciliation.json")
    with open(out_json, "w") as fp:
        json.dump(json_summary, fp, indent=2)
    print("\nSaved Reconciliation JSON to: %s" % out_json)

if __name__ == "__main__":
    main()
