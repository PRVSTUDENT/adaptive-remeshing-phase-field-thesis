#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mode-II Gate M2-4 Adapted Fracture Terminal Evidence Extractor
Extracts full post-processing evidence from Job-2_UEL.odb in Abaqus Python environment:
1. Complete Fx-ux history from Reference Point (RP 999999).
2. Maximum phase-field damage d_max(ux) history from companion UMAT layer (SDV14/SDV1).
3. 5 Target Snapshot datasets at ux = {0.00936, 0.01000, 0.011842, 0.01626, 0.02000} mm.
4. Quantitative phase-field crack trajectory (x, y) coordinates and bottom boundary exit location.
5. Verification of oblique Mode-II propagation direction (rejects horizontal unzipping).
6. Summary JSON with computational metadata, peak force, and trajectory angle.
"""

from __future__ import print_function
import sys
import os
import math
import json

try:
    from odbAccess import openOdb
except ImportError:
    print("[ERROR] odbAccess module not available. Run with 'abaqus python'.")
    sys.exit(1)

def extract_mode2_adapted_fracture_evidence(odb_path, output_dir):
    print("=== Mode-II Gate M2-4 Adapted Fracture Terminal Extractor ===")
    print("ODB Path: %s" % odb_path)
    print("Output Dir: %s" % output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    odb = openOdb(path=odb_path, readOnly=True)
    print("ODB opened successfully.")

    # Target snapshot displacements (in mm)
    target_snaps = [
        {"target_ux": 0.00936, "filename": "damage_snapshot_ux_0p00936.csv", "name": "Pre-Peak (9.36 um)"},
        {"target_ux": 0.01000, "filename": "damage_snapshot_ux_0p01000.csv", "name": "Step-1 Final (10.0 um)"},
        {"target_ux": 0.011842, "filename": "damage_snapshot_ux_0p01184.csv", "name": "Peak Damage (11.842 um)"},
        {"target_ux": 0.01626, "filename": "damage_snapshot_ux_0p01626.csv", "name": "Post-Peak Softening (16.26 um)"},
        {"target_ux": 0.02000, "filename": "damage_snapshot_ux_0p02000.csv", "name": "Terminal Full Horizon (20.0 um)"}
    ]

    rf_history = []
    dmax_history = []
    
    # 1. Reaction force and displacement from RP history output
    rp_step_data = []
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        print("Processing Step: %s (Total Frames: %d)" % (step_name, len(step.frames)))
        
        # History region for RP
        for h_key in step.historyRegions.keys():
            if "999999" in h_key or "N_RP" in h_key or "ASSEMBLY" in h_key.upper():
                hr = step.historyRegions[h_key]
                if 'RF1' in hr.historyOutputs and 'U1' in hr.historyOutputs:
                    rf_vals = hr.historyOutputs['RF1'].data
                    u_vals = hr.historyOutputs['U1'].data
                    for (t_u, u_val), (t_rf, rf_val) in zip(u_vals, rf_vals):
                        rf_history.append((step_name, t_u, u_val, rf_val))
                    break

    # If history region not directly populated, extract from field outputs
    if len(rf_history) == 0:
        print("Extracting RF from field outputs...")
        for step_name in odb.steps.keys():
            step = odb.steps[step_name]
            for frame_idx, frame in enumerate(step.frames):
                t = frame.frameValue
                u_field = frame.fieldOutputs.get('U', None)
                rf_field = frame.fieldOutputs.get('RF', None)
                
                ux_val = None
                rf_val = None
                
                if u_field is not None:
                    for val in u_field.values:
                        if val.nodeLabel == 999999:
                            ux_val = val.data[0]
                            break
                if rf_field is not None:
                    for val in rf_field.values:
                        if val.nodeLabel == 999999:
                            rf_val = val.data[0]
                            break
                            
                if ux_val is not None and rf_val is not None:
                    rf_history.append((step_name, t, ux_val, rf_val))

    print("Extracted %d RF-U history points." % len(rf_history))

    # Save RF history
    rf_csv_path = os.path.join(output_dir, "mode2_j2_rf_history.csv")
    with open(rf_csv_path, "w") as f:
        f.write("step_name,frame_time,ux_mm,rf1_kN\n")
        for s_name, t, ux, rf1 in rf_history:
            f.write("%s,%.8e,%.8e,%.8e\n" % (s_name, t, ux, rf1))

    # 2. Extract d_max history and find closest frames for target snapshots
    snap_frames = {}
    for snap in target_snaps:
        snap_frames[snap["target_ux"]] = {"min_diff": 1e9, "frame": None, "step": None, "actual_ux": None}

    print("Extracting d_max history and locating target snapshots...")
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        for frame_idx, frame in enumerate(step.frames):
            t = frame.frameValue
            
            # Find frame ux
            current_ux = None
            if 'U' in frame.fieldOutputs:
                for val in frame.fieldOutputs['U'].values:
                    if val.nodeLabel == 999999:
                        current_ux = val.data[0]
                        break
            if current_ux is None:
                # Estimate from step time
                if step_name == 'Step-1':
                    current_ux = t * 0.0100
                else:
                    current_ux = 0.0100 + t * 0.0100

            # Find d_max from SDV field
            max_d = 0.0
            if 'SDV' in frame.fieldOutputs:
                sdv_field = frame.fieldOutputs['SDV']
                for val in sdv_field.values:
                    if len(val.data) >= 14:
                        d_val = val.data[13] # SDV14 (0-based idx 13)
                        if d_val > max_d:
                            max_d = d_val
                    elif len(val.data) >= 1:
                        d_val = val.data[0] # SDV1 fallback
                        if d_val > max_d:
                            max_d = d_val
                            
            dmax_history.append((step_name, t, current_ux, max_d))

            # Check snapshot match
            for snap in target_snaps:
                diff = abs(current_ux - snap["target_ux"])
                if diff < snap_frames[snap["target_ux"]]["min_diff"]:
                    snap_frames[snap["target_ux"]]["min_diff"] = diff
                    snap_frames[snap["target_ux"]]["frame"] = frame
                    snap_frames[snap["target_ux"]]["step"] = step_name
                    snap_frames[snap["target_ux"]]["actual_ux"] = current_ux

    # Save d_max history
    dmax_csv_path = os.path.join(output_dir, "mode2_j2_dmax_history.csv")
    with open(dmax_csv_path, "w") as f:
        f.write("step_name,frame_time,ux_mm,d_max\n")
        for s_name, t, ux, d_max in dmax_history:
            f.write("%s,%.8e,%.8e,%.8e\n" % (s_name, t, ux, d_max))

    # 3. Save Snapshots
    for snap in target_snaps:
        info = snap_frames[snap["target_ux"]]
        frame = info["frame"]
        if frame is None:
            print("[WARN] Snapshot for ux=%.5f not found." % snap["target_ux"])
            continue

        print("Saving snapshot for ux=%.5f (actual=%.5f, step=%s) -> %s" % 
              (snap["target_ux"], info["actual_ux"], info["step"], snap["filename"]))
        snap_path = os.path.join(output_dir, snap["filename"])

        # Extract element phase values
        element_d = {}
        if 'SDV' in frame.fieldOutputs:
            for val in frame.fieldOutputs['SDV'].values:
                eid = val.elementLabel
                # Companion elements are in layer 3: 45061..67590 (phys eid = eid - 45060)
                if 45061 <= eid <= 67590:
                    phys_eid = eid - 45060
                    if len(val.data) >= 14:
                        element_d[phys_eid] = val.data[13]
                    elif len(val.data) >= 1:
                        element_d[phys_eid] = val.data[0]

        with open(snap_path, "w") as f:
            f.write("element_id,d\n")
            for peid in sorted(element_d.keys()):
                f.write("%d,%.8e\n" % (peid, element_d[peid]))

    # 4. Extract Phase-Field Crack Trajectory from Terminal State
    terminal_snap = target_snaps[-1]
    term_frame = snap_frames[terminal_snap["target_ux"]]["frame"]
    crack_trajectory = []
    bottom_exit_x = None
    chord_angle_deg = None

    if term_frame is not None:
        print("Extracting Crack Trajectory from terminal frame...")
        # Get element centroids from instance
        inst = odb.rootAssembly.instances.values()[0] if len(odb.rootAssembly.instances) > 0 else None
        
        # Build node coordinates
        node_coords = {}
        if inst is not None:
            for n in inst.nodes:
                node_coords[n.label] = (n.coordinates[0], n.coordinates[1])
                
        # Centroids and d values for physical elements
        centroids = {}
        if inst is not None:
            for elem in inst.elements:
                if 1 <= elem.label <= 22530:
                    pts = [node_coords[nl] for nl in elem.connectivity if nl in node_coords]
                    if len(pts) > 0:
                        cx = sum(p[0] for p in pts) / float(len(pts))
                        cy = sum(p[1] for p in pts) / float(len(pts))
                        centroids[elem.label] = (cx, cy)

        # Map terminal d
        term_d = {}
        if 'SDV' in term_frame.fieldOutputs:
            for val in term_frame.fieldOutputs['SDV'].values:
                if 45061 <= val.elementLabel <= 67590:
                    peid = val.elementLabel - 45060
                    term_d[peid] = val.data[13] if len(val.data) >= 14 else val.data[0]

        # Extract crack points: for each x-slice, find y of maximum d where d > 0.5
        x_bins = {}
        for peid, (cx, cy) in centroids.items():
            d_val = term_d.get(peid, 0.0)
            if d_val > 0.5 and cx >= 0.50: # Starting from crack tip x >= 0.50
                x_key = round(cx, 2)
                if x_key not in x_bins or d_val > x_bins[x_key]["max_d"]:
                    x_bins[x_key] = {"max_d": d_val, "x": cx, "y": cy}

        for x_k in sorted(x_bins.keys()):
            crack_trajectory.append((x_bins[x_k]["x"], x_bins[x_k]["y"], x_bins[x_k]["max_d"]))

        # Sort trajectory along x
        crack_trajectory.sort(key=lambda p: p[0])

        if len(crack_trajectory) >= 2:
            tip_x, tip_y = 0.50, 0.50
            last_x, last_y = crack_trajectory[-1][0], crack_trajectory[-1][1]
            dx = last_x - tip_x
            dy = last_y - tip_y
            chord_angle_deg = math.degrees(math.atan2(dy, dx))
            
            # Extrapolate to y = 0.0 to estimate bottom exit
            if abs(dy) > 1e-4:
                bottom_exit_x = tip_x + (0.0 - tip_y) * (dx / dy)
            else:
                bottom_exit_x = last_x

        print("Crack Trajectory extracted: %d points." % len(crack_trajectory))
        print("Estimated bottom exit: x = %.4f mm, chord angle = %.2f deg" % 
              (bottom_exit_x if bottom_exit_x is not None else 0.0,
               chord_angle_deg if chord_angle_deg is not None else 0.0))

    # Save trajectory CSV
    traj_csv_path = os.path.join(output_dir, "mode2_j2_crack_trajectory.csv")
    with open(traj_csv_path, "w") as f:
        f.write("x_mm,y_mm,d\n")
        for x, y, d in crack_trajectory:
            f.write("%.6e,%.6e,%.6e\n" % (x, y, d))

    # 5. Compute Peak Force and Summary Metrics
    f_max = 0.0
    u_at_fmax = 0.0
    for s_name, t, ux, rf1 in rf_history:
        if rf1 > f_max:
            f_max = rf1
            u_at_fmax = ux

    final_rf = rf_history[-1][3] if len(rf_history) > 0 else 0.0
    final_ux = rf_history[-1][2] if len(rf_history) > 0 else 0.0
    final_dmax = dmax_history[-1][3] if len(dmax_history) > 0 else 0.0

    summary = {
        "job_name": "Job-2_UEL",
        "benchmark": "Pandey & Kumar (2025) Mode-II Adapted Fracture",
        "element_count": 22530,
        "nodes_count": 22642,
        "f_max_kN": f_max,
        "u_at_fmax_mm": u_at_fmax,
        "final_ux_mm": final_ux,
        "final_rf_kN": final_rf,
        "final_dmax": final_dmax,
        "bottom_exit_x_mm": bottom_exit_x,
        "chord_angle_deg": chord_angle_deg,
        "trajectory_points_count": len(crack_trajectory),
        "total_rf_history_points": len(rf_history),
        "total_dmax_history_points": len(dmax_history),
        "is_oblique_mode2_crack": bool(chord_angle_deg is not None and chord_angle_deg < -30.0 and bottom_exit_x is not None and bottom_exit_x > 0.80)
    }

    summary_json_path = os.path.join(output_dir, "MODE2_M2_4_TERMINAL_EXTRACTION_SUMMARY.json")
    with open(summary_json_path, "w") as f:
        json.dump(summary, f, indent=2)

    odb.close()
    print("=== EXTRACTION COMPLETE. Summary saved to %s ===" % summary_json_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        odb_p = "Job-2_UEL.odb"
        out_d = "."
    else:
        odb_p = sys.argv[1]
        out_d = sys.argv[2] if len(sys.argv) >= 3 else "."
    extract_mode2_adapted_fracture_evidence(odb_p, out_d)
