"""
Mode-II Gate M2-4 Adapted Fracture Direct-Frame Terminal Evidence Extractor
Executes in ~5 seconds by:
1. Parsing RF-U history directly from Job-2_UEL.dat (all 4,000 increments)
2. Parsing physical element connectivity and node coordinates from Job-2_UEL.inp
3. Accessing ONLY the 5 specific target frames in Job-2_UEL.odb (O(1) frame lookup)
4. Extracting damage fields (SDV14/SDV), crack trajectory, chord angle, and bottom exit location
5. Outputting summary JSON and all 5 publication snapshot CSVs
"""

import os
import sys
import json
import math

def run_fast_extraction(work_dir="/scratch9/pr21vyci/runs/mode2_j2_adapted_fracture"):
    dat_path = os.path.join(work_dir, "Job-2_UEL.dat")
    inp_path = os.path.join(work_dir, "Job-2_UEL.inp")
    odb_path = os.path.join(work_dir, "Job-2_UEL.odb")

    print("=" * 75)
    print("MODE-II GATE M2-4 FAST TERMINAL EVIDENCE EXTRACTOR")
    print("Work Dir: %s" % work_dir)
    print("=" * 75)

    # ---------------------------------------------------------
    # 1. Parse RF-U History from DAT file
    # ---------------------------------------------------------
    print("[1/5] Parsing Reaction Force history from %s..." % dat_path)
    rf_history = []
    if os.path.exists(dat_path):
        with open(dat_path, "r") as f:
            for line in f:
                if "999999" in line:
                    parts = line.split()
                    if len(parts) == 3 and parts[0] == "999999":
                        try:
                            u1 = float(parts[1])
                            rf1 = float(parts[2])
                            step_str = "Step-1" if u1 <= 0.010000000001 else "Step-2"
                            rf_history.append((step_str, u1, rf1))
                        except ValueError:
                            pass

    print("Extracted %d RF-U data points from DAT file." % len(rf_history))
    
    rf_csv_path = os.path.join(work_dir, "mode2_j2_rf_history.csv")
    with open(rf_csv_path, "w") as out_f:
        out_f.write("step_name,frame_time,ux_mm,rf1_kN\n")
        for s_name, ux, rf1 in rf_history:
            out_f.write("%s,0.0,%.8e,%.8e\n" % (s_name, ux, rf1))
    print("Saved RF history -> %s" % rf_csv_path)

    # Compute F_max, u(F_max), and initial shear stiffness K0
    f_max = 0.0
    u_at_fmax = 0.0
    for s_name, ux, rf1 in rf_history:
        if rf1 > f_max:
            f_max = rf1
            u_at_fmax = ux

    # Initial shear stiffness K0 for u_x <= 0.005 mm
    k0_pts = [(ux, rf1) for s_name, ux, rf1 in rf_history if 0.0005 <= ux <= 0.0050]
    k0_shear = 0.0
    if len(k0_pts) >= 5:
        ux_vals = [p[0] for p in k0_pts]
        rf_vals = [p[1] for p in k0_pts]
        mean_u = sum(ux_vals) / float(len(ux_vals))
        mean_rf = sum(rf_vals) / float(len(rf_vals))
        num = sum((ux_vals[i] - mean_u) * (rf_vals[i] - mean_rf) for i in range(len(ux_vals)))
        den = sum((ux_vals[i] - mean_u) ** 2 for i in range(len(ux_vals)))
        if den > 1e-12:
            k0_shear = num / den

    final_ux = rf_history[-1][1] if len(rf_history) > 0 else 0.0
    final_rf = rf_history[-1][2] if len(rf_history) > 0 else 0.0
    drop_pct = ((f_max - final_rf) / f_max * 100.0) if f_max > 0.0 else 0.0

    print("Initial Shear Stiffness K0 = %.4f kN/mm" % k0_shear)
    print("Peak Force F_max = %.6f kN (%.2f N) at u_x = %.6f mm (%.2f um)" % 
          (f_max, f_max * 1000.0, u_at_fmax, u_at_fmax * 1000.0))
    print("Final Force F(20um) = %.6f kN (%.2f N), Softening Drop = %.2f%%" % 
          (final_rf, final_rf * 1000.0, drop_pct))

    # ---------------------------------------------------------
    # 2. Parse Nodes and Physical Elements from INP file
    # ---------------------------------------------------------
    print("[2/5] Parsing mesh topology from %s..." % inp_path)
    nodes = {}
    elements = {}
    n_phys = 22530

    if os.path.exists(inp_path):
        in_node_section = False
        in_elem_section = False
        with open(inp_path, "r") as f:
            for line in f:
                l = line.strip()
                if not l:
                    continue
                if l.startswith("*"):
                    upper_l = l.upper()
                    if upper_l.startswith("*NODE") and not upper_l.startswith("*NODE OUTPUT") and not upper_l.startswith("*NODE PRINT") and not upper_l.startswith("*NODEFILE"):
                        in_node_section = True
                        in_elem_section = False
                        continue
                    elif upper_l.startswith("*ELEMENT"):
                        in_node_section = False
                        if "TYPE=U1" in upper_l or "TYPE=U3" in upper_l or "ELSET=PHASE" in upper_l:
                            in_elem_section = True
                        else:
                            in_elem_section = False
                        continue
                    elif upper_l.startswith("*"):
                        in_node_section = False
                        in_elem_section = False
                        continue

                if in_node_section:
                    parts = l.split(",")
                    if len(parts) >= 3:
                        try:
                            nid = int(parts[0].strip())
                            x = float(parts[1].strip())
                            y = float(parts[2].strip())
                            nodes[nid] = (x, y)
                        except ValueError:
                            pass

                if in_elem_section:
                    parts = l.split(",")
                    if len(parts) >= 4:
                        try:
                            eid = int(parts[0].strip())
                            if eid <= n_phys:
                                conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                                elements[eid] = conn
                        except ValueError:
                            pass

    print("Parsed %d nodes and %d physical elements from INP." % (len(nodes), len(elements)))

    # Compute centroids for physical elements
    centroids = {}
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if pts:
            xc = sum(p[0] for p in pts) / float(len(pts))
            yc = sum(p[1] for p in pts) / float(len(pts))
            centroids[eid] = (xc, yc)

    # ---------------------------------------------------------
    # 3. Access Specific Frames in ODB for Damage Fields
    # ---------------------------------------------------------
    print("[3/5] Opening ODB for direct-frame damage extraction: %s..." % odb_path)
    from odbAccess import openOdb
    odb = openOdb(path=odb_path, readOnly=True)

    # Target snapshots specification
    target_snaps = [
        {"target_ux": 0.00936, "step_name": "Step-1", "frame_idx": 936, "filename": "damage_snapshot_ux_0p00936.csv", "name": "Pre-Peak (9.36 um)"},
        {"target_ux": 0.01000, "step_name": "Step-1", "frame_idx": 1000, "filename": "damage_snapshot_ux_0p01000.csv", "name": "Step-1 Final (10.0 um)"},
        {"target_ux": 0.011842, "step_name": "Step-2", "frame_idx": 184, "filename": "damage_snapshot_ux_0p01184.csv", "name": "Peak Damage (11.842 um)"},
        {"target_ux": 0.01626, "step_name": "Step-2", "frame_idx": 626, "filename": "damage_snapshot_ux_0p01626.csv", "name": "Post-Peak Softening (16.26 um)"},
        {"target_ux": 0.02000, "step_name": "Step-2", "frame_idx": 1000, "filename": "damage_snapshot_ux_0p02000.csv", "name": "Terminal Full Horizon (20.0 um)"}
    ]

    dmax_history = []
    layer3_start = 2 * n_phys + 1
    layer3_end = 3 * n_phys

    for snap in target_snaps:
        s_name = snap["step_name"]
        f_idx = snap["frame_idx"]
        step = odb.steps[s_name]
        
        # Safe frame index clamping
        if f_idx >= len(step.frames):
            f_idx = len(step.frames) - 1
        frame = step.frames[f_idx]
        actual_t = float(frame.frameValue)
        actual_ux = (actual_t * 0.0100) if s_name == "Step-1" else (0.0100 + actual_t * 0.0100)

        print("Extracting snapshot '%s' from %s frame %d (actual ux = %.5f mm)..." % 
              (snap["name"], s_name, f_idx, actual_ux))

        element_d = {}
        max_d = 0.0

        # Check SDV14 first, then fallback to SDV
        if 'SDV14' in frame.fieldOutputs:
            fo_sdv = frame.fieldOutputs['SDV14']
            for val in fo_sdv.values:
                eid = val.elementLabel
                if layer3_start <= eid <= layer3_end:
                    peid = eid - 2 * n_phys
                    d_val = float(val.data) if isinstance(val.data, (int, float)) else float(val.data[0])
                    element_d[peid] = d_val
                    if d_val > max_d:
                        max_d = d_val
        elif 'SDV' in frame.fieldOutputs:
            fo_sdv = frame.fieldOutputs['SDV']
            for val in fo_sdv.values:
                eid = val.elementLabel
                if layer3_start <= eid <= layer3_end:
                    peid = eid - 2 * n_phys
                    d_val = float(val.data[13]) if len(val.data) >= 14 else float(val.data[0])
                    element_d[peid] = d_val
                    if d_val > max_d:
                        max_d = d_val

        dmax_history.append((s_name, actual_t, actual_ux, max_d))
        snap["element_d"] = element_d
        snap["max_d"] = max_d
        snap["actual_ux"] = actual_ux

        # Save snapshot CSV
        snap_csv_path = os.path.join(work_dir, snap["filename"])
        with open(snap_csv_path, "w") as sf:
            sf.write("element_id,d\n")
            for peid in sorted(element_d.keys()):
                sf.write("%d,%.8e\n" % (peid, element_d[peid]))
        print("  -> Saved %d element damage values (d_max = %.4f) to %s" % 
              (len(element_d), max_d, snap_csv_path))

    # Save d_max summary history
    dmax_csv_path = os.path.join(work_dir, "mode2_j2_dmax_history.csv")
    with open(dmax_csv_path, "w") as df:
        df.write("step_name,frame_time,ux_mm,d_max\n")
        for s_name, t, ux, d_val in dmax_history:
            df.write("%s,%.8e,%.8e,%.8e\n" % (s_name, t, ux, d_val))
    print("Saved d_max history -> %s" % dmax_csv_path)

    # ---------------------------------------------------------
    # 4. Extract Crack Trajectory from Terminal State (20 um)
    # ---------------------------------------------------------
    print("[4/5] Extracting Phase-Field Crack Trajectory from terminal state...")
    term_snap = target_snaps[-1]
    term_d = term_snap["element_d"]
    crack_trajectory = []
    bottom_exit_x = None
    chord_angle_deg = None

    # Group elements with d >= 0.50 and x >= 0.48 into x-bins (dx = 0.01 mm)
    x_bins = {}
    for peid, (cx, cy) in centroids.items():
        d_val = term_d.get(peid, 0.0)
        if d_val >= 0.50 and cx >= 0.48:
            bin_idx = int(math.floor(cx / 0.01))
            if bin_idx not in x_bins or d_val > x_bins[bin_idx]["max_d"]:
                x_bins[bin_idx] = {"max_d": d_val, "x": cx, "y": cy}

    for bin_idx in sorted(x_bins.keys()):
        crack_trajectory.append((x_bins[bin_idx]["x"], x_bins[bin_idx]["y"], x_bins[bin_idx]["max_d"]))

    crack_trajectory.sort(key=lambda p: p[0])

    if len(crack_trajectory) >= 2:
        tip_x, tip_y = 0.50, 0.50
        prop_points = [p for p in crack_trajectory if p[0] >= 0.52]
        if prop_points:
            last_x, last_y = prop_points[-1][0], prop_points[-1][1]
            dx = last_x - tip_x
            dy = last_y - tip_y
            chord_angle_deg = math.degrees(math.atan2(dy, dx))
            
            # Extrapolate to bottom edge (y = 0.0)
            if abs(dy) > 1e-4:
                bottom_exit_x = tip_x + (0.0 - tip_y) * (dx / dy)
            else:
                bottom_exit_x = last_x

    print("Crack Trajectory extracted: %d points." % len(crack_trajectory))
    print("Estimated bottom exit: x = %.4f mm, chord angle = %.2f deg" % 
          (bottom_exit_x if bottom_exit_x is not None else 0.0,
           chord_angle_deg if chord_angle_deg is not None else 0.0))

    traj_csv_path = os.path.join(work_dir, "mode2_j2_crack_trajectory.csv")
    with open(traj_csv_path, "w") as tf:
        tf.write("x_mm,y_mm,d\n")
        for x, y, d in crack_trajectory:
            tf.write("%.6e,%.6e,%.6e\n" % (x, y, d))
    print("Saved crack trajectory -> %s" % traj_csv_path)

    # ---------------------------------------------------------
    # 5. Build Summary JSON
    # ---------------------------------------------------------
    print("[5/5] Generating Gate M2-4 Summary JSON...")
    final_dmax = term_snap["max_d"]

    summary = {
        "job_name": "Job-2_UEL",
        "benchmark": "Pandey & Kumar (2025) Mode-II Adapted Fracture",
        "element_count": n_phys,
        "nodes_count": len(nodes),
        "k0_shear_kN_per_mm": k0_shear,
        "f_max_kN": f_max,
        "f_max_N": f_max * 1000.0,
        "u_at_fmax_mm": u_at_fmax,
        "u_at_fmax_um": u_at_fmax * 1000.0,
        "final_ux_mm": final_ux,
        "final_rf_kN": final_rf,
        "final_rf_N": final_rf * 1000.0,
        "f_at_20um_kN": final_rf,
        "f_at_20um_N": final_rf * 1000.0,
        "softening_drop_pct": drop_pct,
        "final_dmax": final_dmax,
        "bottom_exit_x_mm": bottom_exit_x,
        "chord_angle_deg": chord_angle_deg,
        "trajectory_points_count": len(crack_trajectory),
        "total_rf_history_points": len(rf_history),
        "is_oblique_mode2_crack": bool(chord_angle_deg is not None and chord_angle_deg < -30.0 and bottom_exit_x is not None and bottom_exit_x > 0.80)
    }

    summary_json_path = os.path.join(work_dir, "MODE2_M2_4_TERMINAL_EXTRACTION_SUMMARY.json")
    with open(summary_json_path, "w") as jf:
        json.dump(summary, jf, indent=2)

    odb.close()
    print("=" * 75)
    print("=== EXTRACTION COMPLETE. Summary saved to %s ===" % summary_json_path)
    print("K0_shear = %.4f kN/mm" % k0_shear)
    print("F_max = %.4f kN (%.1f N) at ux = %.4f um" % (f_max, f_max * 1000.0, u_at_fmax * 1000.0))
    print("F(20um) = %.4f kN (%.1f N), Load drop = %.1f%%" % (final_rf, final_rf * 1000.0, drop_pct))
    print("Final d_max = %.4f" % final_dmax)
    print("Estimated Bottom Exit: x = %.4f mm, Chord Angle = %.2f deg" % 
          (bottom_exit_x if bottom_exit_x is not None else 0.0, chord_angle_deg if chord_angle_deg is not None else 0.0))
    print("=" * 75)

if __name__ == "__main__":
    work_d = sys.argv[1] if len(sys.argv) >= 2 else "/scratch9/pr21vyci/runs/mode2_j2_adapted_fracture"
    run_fast_extraction(work_d)
