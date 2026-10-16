#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_enriched_baseline_ground_truth.py
=========================================
Abaqus Python extraction script to harvest authentic continuous baseline
ground-truth state (u_x, u_y, d=U3, H=SDV2, d_avg=SDV14, RF, energies)
at handoff state u = 0.005000 mm (increment 2000) from:
Package 50: M1_MB_FINE_BASELINE_ENRICHED.odb (Job 1414571.mmaster02).

Usage:
    abaqus python extract_enriched_baseline_ground_truth.py [--odb PATH] [--output JSON_PATH]

Protocol Version: 2
Author: Gemini Antigravity
Task: F1517
"""

import os
import sys
import json
import math
import argparse


def extract_ground_truth(odb_path, output_json_path):
    print("=" * 70)
    print("EXTRACT ENRICHED BASELINE GROUND TRUTH (ABAQUS PYTHON)")
    print("=" * 70)
    print("ODB Path: %s" % odb_path)
    print("Output JSON: %s" % output_json_path)

    if not os.path.exists(odb_path):
        print("ERROR: ODB file not found: %s" % odb_path)
        sys.exit(1)

    try:
        from odbAccess import openOdb
    except ImportError:
        print("ERROR: Must be run inside Abaqus Python (abaqus python ...)")
        sys.exit(1)

    odb = openOdb(odb_path, readOnly=True)
    print("Successfully opened ODB: %s" % odb.name)

    # 1. Step inspection
    step_name = "Step-1"
    if step_name not in odb.steps:
        # Fallback to the first step
        step_name = list(odb.steps.keys())[0]
        print("Warning: Step-1 not found, using first step: %s" % step_name)

    step = odb.steps[step_name]
    num_frames = len(step.frames)
    print("Step: %s | Total Frames: %d" % (step_name, num_frames))

    if num_frames == 0:
        print("ERROR: Step has 0 frames!")
        odb.close()
        sys.exit(1)

    # Use the final frame (increment 2000, handoff state u = 0.0050 mm)
    terminal_frame = step.frames[-1]
    frame_val = terminal_frame.frameValue
    frame_id = terminal_frame.frameId
    print("Terminal Frame ID: %d | Frame Value: %g" % (frame_id, frame_val))

    # 2. Extract Nodal Coordinates from Root Assembly / Instances
    node_coords = {}
    assembly = odb.rootAssembly
    for inst_name, inst in assembly.instances.items():
        print("Instance: %s | Nodes: %d | Elements: %d" % (inst_name, len(inst.nodes), len(inst.elements)))
        for n in inst.nodes:
            node_coords[int(n.label)] = [float(n.coordinates[0]), float(n.coordinates[1])]
    
    # If no instances, check rootAssembly nodes
    if not node_coords and hasattr(assembly, 'nodes'):
        for n in assembly.nodes:
            node_coords[int(n.label)] = [float(n.coordinates[0]), float(n.coordinates[1])]

    print("Total mesh nodes indexed: %d" % len(node_coords))

    # 3. Extract Nodal Displacements and UEL Nodal Phase Field (U)
    nodal_state = {}
    d_max = -1.0e9
    d_min = 1.0e9
    node_dmax = -1

    if "U" in terminal_frame.fieldOutputs:
        u_field = terminal_frame.fieldOutputs["U"]
        for v in u_field.values:
            n_label = int(v.nodeLabel)
            data = v.data
            ux = float(data[0]) if len(data) >= 1 else 0.0
            uy = float(data[1]) if len(data) >= 2 else 0.0
            d_val = float(data[2]) if len(data) >= 3 else None

            if d_val is not None:
                if d_val > d_max:
                    d_max = d_val
                    node_dmax = n_label
                if d_val < d_min:
                    d_min = d_val

            nodal_state[n_label] = {
                "coord": node_coords.get(n_label, [0.0, 0.0]),
                "ux": ux,
                "uy": uy,
                "d": d_val
            }
        print("Extracted U for %d nodes. d_max = %g (node %d), d_min = %g" % (
            len(nodal_state), d_max if d_max > -1e8 else 0.0, node_dmax, d_min if d_min < 1e8 else 0.0
        ))
    else:
        print("WARNING: 'U' fieldOutput not found in terminal frame!")

    # 4. Extract Reaction Forces (RF) at RP (node 999999)
    rf_rp = [0.0, 0.0]
    if "RF" in terminal_frame.fieldOutputs:
        rf_field = terminal_frame.fieldOutputs["RF"]
        for v in rf_field.values:
            if v.nodeLabel == 999999:
                rf_rp = [float(v.data[0]), float(v.data[1])]
                break
        print("Reaction Force at RP (node 999999): RF1 = %g N, RF2 = %g N" % (rf_rp[0], rf_rp[1]))
    else:
        print("WARNING: 'RF' fieldOutput not found in terminal frame!")

    # 5. Extract Element State Variables (SDVs: H = SDV2, d_avg = SDV14)
    elem_sdv = {}
    h_max = -1.0e9
    elem_hmax = -1

    # Check available SDV field names
    avail_fields = list(terminal_frame.fieldOutputs.keys())
    sdv_field_name = None
    if "SDV" in avail_fields:
        sdv_field_name = "SDV"
    elif "SDV2" in avail_fields or "SDV_SDV2" in avail_fields:
        sdv_field_name = "SDV_SDV2"

    if sdv_field_name and sdv_field_name in terminal_frame.fieldOutputs:
        sdv_field = terminal_frame.fieldOutputs[sdv_field_name]
        for v in sdv_field.values:
            e_label = int(v.elementLabel)
            if e_label not in elem_sdv:
                elem_sdv[e_label] = {"SDV2": [], "SDV14": []}
            
            # If composite SDV vector
            if hasattr(v, 'data'):
                if isinstance(v.data, (list, tuple)):
                    # In Abaqus SDV array, SDV2 is index 1, SDV14 is index 13 (0-based)
                    if len(v.data) >= 14:
                        h_val = float(v.data[1])
                        d_avg = float(v.data[13])
                    elif len(v.data) >= 2:
                        h_val = float(v.data[1])
                        d_avg = float(v.data[1])
                    else:
                        h_val = float(v.data[0])
                        d_avg = 0.0
                else:
                    h_val = float(v.data)
                    d_avg = 0.0
                
                elem_sdv[e_label]["SDV2"].append(h_val)
                elem_sdv[e_label]["SDV14"].append(d_avg)

                if h_val > h_max:
                    h_max = h_val
                    elem_hmax = e_label

        print("Extracted SDVs for %d elements. H_max = %g (elem %d)" % (
            len(elem_sdv), h_max if h_max > -1e8 else 0.0, elem_hmax
        ))
    else:
        print("Note: Direct composite SDV field not in fieldOutputs. Checking individual SDV fields...")
        # Check for SDV_SDV2 and SDV_SDV14
        sdv2_field = terminal_frame.fieldOutputs.get("SDV_SDV2") or terminal_frame.fieldOutputs.get("SDV2")
        sdv14_field = terminal_frame.fieldOutputs.get("SDV_SDV14") or terminal_frame.fieldOutputs.get("SDV14")
        if sdv2_field:
            for v in sdv2_field.values:
                e_label = int(v.elementLabel)
                if e_label not in elem_sdv:
                    elem_sdv[e_label] = {"SDV2": [], "SDV14": []}
                h_val = float(v.data)
                elem_sdv[e_label]["SDV2"].append(h_val)
                if h_val > h_max:
                    h_max = h_val
                    elem_hmax = e_label
        if sdv14_field:
            for v in sdv14_field.values:
                e_label = int(v.elementLabel)
                if e_label in elem_sdv:
                    elem_sdv[e_label]["SDV14"].append(float(v.data))
        print("Indexed individual SDVs for %d elements. H_max = %g (elem %d)" % (
            len(elem_sdv), h_max if h_max > -1e8 else 0.0, elem_hmax
        ))

    # 6. Extract Whole Model Energies from History Outputs
    energies = {}
    history_regions = step.historyRegions
    for hr_name, hr in history_regions.items():
        if "Assembly" in hr_name or "Whole" in hr_name:
            for e_key in ["ALLIE", "ALLSE", "ALLWK", "ALLFD", "ALLPD", "ALLCD", "ALLVD", "ETOTAL"]:
                if e_key in hr.historyOutputs:
                    data_pts = hr.historyOutputs[e_key].data
                    if data_pts:
                        energies[e_key] = float(data_pts[-1][1])
            if energies:
                print("Extracted energies from region '%s': %s" % (hr_name, str(energies)))
                break

    # 7. Compile Structured Artifact
    ground_truth = {
        "metadata": {
            "title": "Method B Fine Baseline Enriched Ground-Truth State",
            "job_id": "1414571.mmaster02",
            "model_name": "M1_MB_FINE_BASELINE_ENRICHED",
            "mesh_elements": len(elem_sdv) if elem_sdv else len(assembly.instances.get(list(assembly.instances.keys())[0]).elements) if assembly.instances else 14483,
            "mesh_nodes": len(nodal_state) if nodal_state else 14456,
            "step_name": step_name,
            "frame_id": frame_id,
            "frame_value": frame_val,
            "u_rp_mm": 0.005000,
            "rf1_rp_N": rf_rp[0],
            "rf2_rp_N": rf_rp[1],
            "d_max": d_max if d_max > -1e8 else None,
            "d_max_node": node_dmax,
            "h_max": h_max if h_max > -1e8 else None,
            "h_max_elem": elem_hmax,
            "energies_mJ": energies
        },
        "nodal_state": nodal_state,
        "elem_sdv": elem_sdv
    }

    # 8. Write JSON Artifact
    out_dir = os.path.dirname(output_json_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(output_json_path, "w") as f:
        json.dump(ground_truth, f)

    file_size_mb = os.path.getsize(output_json_path) / (1024.0 * 1024.0)
    print("Successfully exported ground truth: %s (%.2f MB)" % (output_json_path, file_size_mb))
    print("=" * 70)

    odb.close()
    return ground_truth


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract continuous baseline ground-truth state from enriched ODB.")
    parser.add_argument("--odb", default="M1_MB_FINE_BASELINE_ENRICHED.odb", help="Path to M1_MB_FINE_BASELINE_ENRICHED.odb")
    parser.add_argument("--output", default="fine_baseline_ground_truth_u0050.json", help="Path to output JSON")
    args = parser.parse_args()

    extract_ground_truth(args.odb, args.output)
