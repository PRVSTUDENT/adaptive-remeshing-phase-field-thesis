"""
Mode-II Gate M2-4 Adapted Fracture High-Performance Terminal Extractor
Extracts:
1. Complete Reaction Force (RF1) vs Prescribed Displacement (ux) history (all 2002 frames)
2. Maximum Phase Field (d_max) vs ux history (sampled at 10-frame stride + target snapshots)
3. 5 Discrete Damage Snapshots at ux = [0.00936, 0.01000, 0.011842, 0.01626, 0.02000] mm
4. Final Crack Trajectory, Chord Angle, and Bottom Boundary Exit Location
5. Summary JSON for Gate M2-4 evaluation and acceptance checks
"""

import os
import sys
import json
import math
from odbAccess import openOdb

def extract_mode2_adapted_fracture_evidence(odb_path="Job-2_UEL.odb", output_dir="."):
    if not os.path.exists(odb_path):
        print("[ERROR] ODB not found: %s" % odb_path)
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("=" * 75)
    print("=== MODE-II GATE M2-4 ADAPTED FRACTURE TERMINAL EVIDENCE EXTRACTOR ===")
    print("ODB Path: %s" % odb_path)
    print("Output Dir: %s" % output_dir)
    print("=" * 75)

    odb = openOdb(path=odb_path, readOnly=True)
    step_names = list(odb.steps.keys())
    print("Available Steps: %s" % step_names)

    inst_name = list(odb.rootAssembly.instances.keys())[0]
    inst = odb.rootAssembly.instances[inst_name]
    nodes = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst.nodes}
    elements = {e.label: list(e.connectivity) for e in inst.elements}
    total_elements = len(elements)
    n_phys = total_elements // 3 if total_elements > 3000 else 22530

    print("Mesh: Total Elements=%d, Co-located Layers=3, Physical FEs=%d, Nodes=%d" % 
          (total_elements, n_phys, len(nodes)))

    # Compute centroids for physical elements (1..n_phys)
    centroids = {}
    for eid in range(1, n_phys + 1):
        if eid in elements:
            conn = elements[eid]
            pts = [nodes[nid] for nid in conn if nid in nodes]
            if pts:
                xc = sum(p[0] for p in pts) / float(len(pts))
                yc = sum(p[1] for p in pts) / float(len(pts))
                centroids[eid] = (xc, yc)
            else:
                centroids[eid] = (0.0, 0.0)

    # Target snapshot displacements (in mm)
    target_snaps = [
        {"target_ux": 0.00936, "filename": "damage_snapshot_ux_0p00936.csv", "name": "Pre-Peak (9.36 um)", "min_diff": 1e9, "frame": None, "step": None, "actual_ux": None},
        {"target_ux": 0.01000, "filename": "damage_snapshot_ux_0p01000.csv", "name": "Step-1 Final (10.0 um)", "min_diff": 1e9, "frame": None, "step": None, "actual_ux": None},
        {"target_ux": 0.011842, "filename": "damage_snapshot_ux_0p01184.csv", "name": "Peak Damage (11.842 um)", "min_diff": 1e9, "frame": None, "step": None, "actual_ux": None},
        {"target_ux": 0.01626, "filename": "damage_snapshot_ux_0p01626.csv", "name": "Post-Peak Softening (16.26 um)", "min_diff": 1e9, "frame": None, "step": None, "actual_ux": None},
        {"target_ux": 0.02000, "filename": "damage_snapshot_ux_0p02000.csv", "name": "Terminal Full Horizon (20.0 um)", "min_diff": 1e9, "frame": None, "step": None, "actual_ux": None}
    ]

    rf_history = []
    dmax_history = []

    for s_idx, s_name in enumerate(step_names):
        step = odb.steps[s_name]
        step_frames = step.frames
        n_frames = len(step_frames)
        print("Processing Step '%s' (%d frames)..." % (s_name, n_frames))

        for f_idx, f in enumerate(step_frames):
            f_val = float(f.frameValue)
            if s_name == "Step-1":
                nominal_ux = f_val * 0.0100
            elif s_name == "Step-2":
                nominal_ux = 0.0100 + f_val * 0.0100
            else:
                nominal_ux = f_val

            rf_x = 0.0
            actual_ux = nominal_ux

            if 'RF' in f.fieldOutputs:
                fo_rf = f.fieldOutputs['RF']
                if len(fo_rf.values) > 0:
                    rf_x = float(fo_rf.values[0].data[0])

            if 'U' in f.fieldOutputs:
                fo_u = f.fieldOutputs['U']
                if len(fo_u.values) > 0:
                    actual_ux = float(fo_u.values[0].data[0])

            rf_history.append((s_name, f_val, actual_ux, rf_x))

            # Sample d_max every 10 frames or at terminal frame
            is_sample_frame = (f_idx % 10 == 0) or (f_idx == n_frames - 1)
            
            # Check snapshot matching
            for snap in target_snaps:
                diff = abs(actual_ux - snap["target_ux"])
                if diff < snap["min_diff"]:
                    snap["min_diff"] = diff
                    snap["frame"] = f
                    snap["step"] = s_name
                    snap["actual_ux"] = actual_ux
                    is_sample_frame = True

            if is_sample_frame and 'SDV' in f.fieldOutputs:
                fo_sdv = f.fieldOutputs['SDV']
                d_max = 0.0
                for val in fo_sdv.values:
                    if len(val.data) >= 14:
                        d = float(val.data[13])
                        if d > d_max:
                            d_max = d
                    elif len(val.data) >= 1:
                        d = float(val.data[0])
                        if d > d_max:
                            d_max = d
                dmax_history.append((s_name, f_val, actual_ux, d_max))

    print("Extracted %d RF points and %d d_max sample points." % (len(rf_history), len(dmax_history)))

    # 1. Save RF history
    rf_csv_path = os.path.join(output_dir, "mode2_j2_rf_history.csv")
    with open(rf_csv_path, "w") as f:
        f.write("step_name,frame_time,ux_mm,rf1_kN\n")
        for s_name, t, ux, rf1 in rf_history:
            f.write("%s,%.8e,%.8e,%.8e\n" % (s_name, t, ux, rf1))
    print("Saved RF history -> %s" % rf_csv_path)

    # 2. Save d_max history
    dmax_csv_path = os.path.join(output_dir, "mode2_j2_dmax_history.csv")
    with open(dmax_csv_path, "w") as f:
        f.write("step_name,frame_time,ux_mm,d_max\n")
        for s_name, t, ux, d_max in dmax_history:
            f.write("%s,%.8e,%.8e,%.8e\n" % (s_name, t, ux, d_max))
    print("Saved d_max history -> %s" % dmax_csv_path)

    # 3. Save Snapshots
    for snap in target_snaps:
        frame = snap["frame"]
        if frame is None:
            print("[WARN] Snapshot for ux=%.5f not found." % snap["target_ux"])
            continue

        print("Saving snapshot for ux=%.5f (actual=%.5f, step=%s, diff=%.2e) -> %s" % 
              (snap["target_ux"], snap["actual_ux"], snap["step"], snap["min_diff"], snap["filename"]))
        snap_path = os.path.join(output_dir, snap["filename"])

        # Extract element phase values on Layer 3 companion elements (2*n_phys+1 .. 3*n_phys)
        element_d = {}
        layer3_start = 2 * n_phys + 1
        layer3_end = 3 * n_phys

        if 'SDV' in frame.fieldOutputs:
            for val in frame.fieldOutputs['SDV'].values:
                eid = val.elementLabel
                if layer3_start <= eid <= layer3_end:
                    phys_eid = eid - 2 * n_phys
                    if len(val.data) >= 14:
                        element_d[phys_eid] = float(val.data[13])
                    elif len(val.data) >= 1:
                        element_d[phys_eid] = float(val.data[0])

        with open(snap_path, "w") as f:
            f.write("element_id,d\n")
            for peid in sorted(element_d.keys()):
                f.write("%d,%.8e\n" % (peid, element_d[peid]))

    # 4. Extract Crack Trajectory from Terminal Frame (ux = 0.02000 mm)
    term_snap = target_snaps[-1]
    term_frame = term_snap["frame"]
    crack_trajectory = []
    bottom_exit_x = None
    chord_angle_deg = None

    if term_frame is not None:
        print("Extracting Crack Trajectory from terminal frame (ux=%.5f)..." % term_snap["actual_ux"])
        layer3_start = 2 * n_phys + 1
        layer3_end = 3 * n_phys
        term_d = {}

        if 'SDV' in term_frame.fieldOutputs:
            for val in term_frame.fieldOutputs['SDV'].values:
                eid = val.elementLabel
                if layer3_start <= eid <= layer3_end:
                    phys_eid = eid - 2 * n_phys
                    term_d[phys_eid] = float(val.data[13]) if len(val.data) >= 14 else float(val.data[0])

        # Find elements with significant damage (d >= 0.5) to the right of crack tip (x >= 0.48)
        x_bins = {}
        for peid, (cx, cy) in centroids.items():
            d_val = term_d.get(peid, 0.0)
            if d_val >= 0.50 and cx >= 0.48:
                bin_idx = int(math.floor(cx / 0.01))
                if bin_idx not in x_bins or d_val > x_bins[bin_idx]["max_d"]:
                    x_bins[bin_idx] = {"max_d": d_val, "x": cx, "y": cy}

        for bin_idx in sorted(x_bins.keys()):
            crack_trajectory.append((x_bins[bin_idx]["x"], x_bins[bin_idx]["y"], x_bins[bin_idx]["max_d"]))

        # Sort trajectory along x
        crack_trajectory.sort(key=lambda p: p[0])

        if len(crack_trajectory) >= 2:
            tip_x, tip_y = 0.50, 0.50
            prop_points = [p for p in crack_trajectory if p[0] >= 0.52]
            if prop_points:
                last_x, last_y = prop_points[-1][0], prop_points[-1][1]
                dx = last_x - tip_x
                dy = last_y - tip_y
                chord_angle_deg = math.degrees(math.atan2(dy, dx))
                
                # Extrapolate to y = 0.0 (bottom edge)
                if abs(dy) > 1e-4:
                    bottom_exit_x = tip_x + (0.0 - tip_y) * (dx / dy)
                else:
                    bottom_exit_x = last_x

        print("Crack Trajectory extracted: %d points." % len(crack_trajectory))
        print("Estimated bottom exit: x = %.4f mm, chord angle = %.2f deg" % 
              (bottom_exit_x if bottom_exit_x is not None else 0.0,
               chord_angle_deg if chord_angle_deg is not None else 0.0))

    # Save crack trajectory CSV
    traj_csv_path = os.path.join(output_dir, "mode2_j2_crack_trajectory.csv")
    with open(traj_csv_path, "w") as f:
        f.write("x_mm,y_mm,d\n")
        for x, y, d in crack_trajectory:
            f.write("%.6e,%.6e,%.6e\n" % (x, y, d))
    print("Saved crack trajectory -> %s" % traj_csv_path)

    # 5. Compute Peak Force, Softening, and Summary Metrics
    f_max = 0.0
    u_at_fmax = 0.0
    for s_name, t, ux, rf1 in rf_history:
        if rf1 > f_max:
            f_max = rf1
            u_at_fmax = ux

    final_rf = rf_history[-1][3] if len(rf_history) > 0 else 0.0
    final_ux = rf_history[-1][2] if len(rf_history) > 0 else 0.0
    final_dmax = dmax_history[-1][3] if len(dmax_history) > 0 else 0.0

    # Find reaction force at softening horizon ux = 0.02000 mm
    f_at_20um = final_rf
    softening_drop_pct = ((f_max - f_at_20um) / f_max * 100.0) if f_max > 0.0 else 0.0

    summary = {
        "job_name": "Job-2_UEL",
        "benchmark": "Pandey & Kumar (2025) Mode-II Adapted Fracture",
        "element_count": n_phys,
        "nodes_count": len(nodes),
        "f_max_kN": f_max,
        "f_max_N": f_max * 1000.0,
        "u_at_fmax_mm": u_at_fmax,
        "u_at_fmax_um": u_at_fmax * 1000.0,
        "final_ux_mm": final_ux,
        "final_rf_kN": final_rf,
        "final_rf_N": final_rf * 1000.0,
        "f_at_20um_kN": f_at_20um,
        "f_at_20um_N": f_at_20um * 1000.0,
        "softening_drop_pct": softening_drop_pct,
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
    print("=" * 75)
    print("=== EXTRACTION COMPLETE. Summary saved to %s ===" % summary_json_path)
    print("F_max = %.4f kN (%.1f N) at ux = %.4f um" % (f_max, f_max * 1000.0, u_at_fmax * 1000.0))
    print("F(20um) = %.4f kN (%.1f N), Load drop = %.1f%%" % (f_at_20um, f_at_20um * 1000.0, softening_drop_pct))
    print("Final d_max = %.4f" % final_dmax)
    print("Estimated Bottom Exit: x = %.4f mm, Chord Angle = %.2f deg" % 
          (bottom_exit_x if bottom_exit_x is not None else 0.0, chord_angle_deg if chord_angle_deg is not None else 0.0))
    print("=" * 75)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        odb_p = "Job-2_UEL.odb"
        out_d = "."
    else:
        odb_p = sys.argv[1]
        out_d = sys.argv[2] if len(sys.argv) >= 3 else "."
    extract_mode2_adapted_fracture_evidence(odb_p, out_d)
