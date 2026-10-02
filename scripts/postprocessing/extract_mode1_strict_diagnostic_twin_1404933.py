#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_mode1_strict_diagnostic_twin_1404933.py
------------------------------------------------
Authoritative Terminal Evaluation and Extraction Pipeline for:
Job 1404933.mmaster02 (PK_M1_NOM1_STRICT_0062)

Executes the frozen terminal comparison protocol:
1. Complete U-RF history extraction & SHA-256 hash.
2. Canonical K0 linear regression on [0, 0.001000 mm].
3. Peak force F_max, peak displacement u_peak, final endpoint.
4. Pairwise comparison vs Baseline Job 1404454 (common interval [0, 0.006200 mm]):
   - Max diff, mean diff, discrete RMS, continuous L2 norm
   - 1 N, 5 N, 10 N divergence threshold crossings
   - External work integral W_ext = int F du
5. Solver telemetry (.sta, .msg, PBS accounting).
6. Spatial damage field SDV14 extraction at target checkpoints:
   u = 0.0050, 0.0055, 0.00575, 0.0060, 0.006200 mm
7. Crack tip localization, horizontal/transverse profiles, crack ridge symmetry.
8. Companion layer mechanical neutrality verification.
"""

import os
import sys
import time
import math
import json
import csv
import hashlib

def compute_sha256(filepath):
    if not filepath or not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def compute_array_sha256(u_arr, f_arr):
    h = hashlib.sha256()
    for u, f in zip(u_arr, f_arr):
        h.update(("%.10e,%.10e\n" % (u, f)).encode('utf-8'))
    return h.hexdigest().lower()

def linear_regression_ols(x, y):
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    x_mean = sum(x) / float(n)
    y_mean = sum(y) / float(n)
    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_yy = sum((yi - y_mean) ** 2 for yi in y)
    if ss_xx <= 0.0:
        return 0.0, 0.0, 0.0
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    r2 = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0.0 else 1.0
    return float(slope), float(intercept), float(r2)

def trapezoidal_work(u, f):
    w = 0.0
    for i in range(len(u) - 1):
        du = u[i+1] - u[i]
        f_avg = 0.5 * (f[i+1] + f[i])
        w += f_avg * du
    return float(w)

def interp_1d(x_eval, x_known, y_known):
    res = []
    for x in x_eval:
        if x <= x_known[0]:
            res.append(float(y_known[0]))
        elif x >= x_known[-1]:
            res.append(float(y_known[-1]))
        else:
            low = 0
            high = len(x_known) - 1
            while high - low > 1:
                mid = (low + high) // 2
                if x_known[mid] <= x:
                    low = mid
                else:
                    high = mid
            dx = x_known[high] - x_known[low]
            if dx == 0.0:
                res.append(float(y_known[low]))
            else:
                t = (x - x_known[low]) / dx
                res.append(float(y_known[low] + t * (y_known[high] - y_known[low])))
    return res

def parse_sta_file(sta_path):
    if not sta_path or not os.path.exists(sta_path):
        return None
    increments = []
    total_iters = 0
    total_cutbacks = 0
    min_dt = float('inf')
    with open(sta_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('SUMMARY') or l.startswith('STEP') or l.startswith('INCREMENT') or l.startswith('Abaqus'):
                continue
            parts = l.split()
            if len(parts) >= 8 and parts[0].isdigit() and parts[1].isdigit():
                step = int(parts[0])
                inc = int(parts[1])
                att_str = parts[2]
                n_att = int(''.join(c for c in att_str if c.isdigit())) if any(c.isdigit() for c in att_str) else 1
                n_sev = int(parts[3])
                n_eq = int(parts[4])
                total_iters += n_eq
                if 'U' in att_str or n_att > 1:
                    total_cutbacks += 1
                step_time = float(parts[6])
                total_time = float(parts[7])
                dt = float(parts[8]) if len(parts) > 8 else 0.0
                if dt > 0.0 and dt < min_dt:
                    min_dt = dt
                increments.append({
                    'step': step, 'inc': inc, 'att': n_att, 'sev': n_sev, 'eq': n_eq,
                    'step_time': step_time, 'total_time': total_time, 'dt': dt
                })
    return {
        'total_increments': len(increments),
        'total_iterations': total_iters,
        'total_cutbacks': total_cutbacks,
        'min_dt': min_dt if min_dt != float('inf') else 0.0,
        'last_step': increments[-1]['step'] if increments else 0,
        'last_inc': increments[-1]['inc'] if increments else 0,
        'last_step_time': increments[-1]['step_time'] if increments else 0.0,
        'last_total_time': increments[-1]['total_time'] if increments else 0.0
    }

def load_csv_curve(csv_path):
    u_vals = []
    f_vals = []
    if not os.path.exists(csv_path):
        return u_vals, f_vals
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = None
        u_col = 0
        f_col = 1
        for row in reader:
            if not row or not any(c.strip() for c in row):
                continue
            if header is None:
                try:
                    float(row[0].strip())
                except ValueError:
                    header = [c.strip().lower() for c in row]
                    if 'u2_mm' in header and 'rf2_kn' in header:
                        u_col = header.index('u2_mm')
                        f_col = header.index('rf2_kn')
                    elif 'displacement_mm' in header and 'reaction_force_kn' in header:
                        u_col = header.index('displacement_mm')
                        f_col = header.index('reaction_force_kn')
                    elif 'u_mm' in header and 'rf_kn' in header:
                        u_col = header.index('u_mm')
                        f_col = header.index('rf_kn')
                    continue
            try:
                u = float(row[u_col].strip())
                f = float(row[f_col].strip())
                u_vals.append(u)
                f_vals.append(f)
            except (ValueError, IndexError):
                continue
    # Sort and remove duplicates
    paired = sorted(zip(u_vals, f_vals), key=lambda x: x[0])
    u_clean = []
    f_clean = []
    for u, f in paired:
        if not u_clean or abs(u - u_clean[-1]) > 1e-12:
            u_clean.append(u)
            f_clean.append(f)
    return u_clean, f_clean

def extract_from_odb(odb_path, out_csv_path=None):
    try:
        from odbAccess import openOdb
    except ImportError:
        print("[ERROR] odbAccess not available. Run under Abaqus Python.")
        sys.exit(1)

    t0 = time.time()
    print("Opening ODB (read-only): %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    print("Opened ODB in %.2fs" % (time.time() - t0))

    root = odb.rootAssembly
    inst = list(root.instances.values())[0] if len(root.instances) > 0 else root
    
    ntop = root.nodeSets['N_TOP'] if 'N_TOP' in root.nodeSets else inst.nodeSets['N_TOP']
    nbot = root.nodeSets['N_BOTTOM'] if 'N_BOTTOM' in root.nodeSets else inst.nodeSets['N_BOTTOM']
    n_top_count = len(ntop.nodes[0]) if hasattr(ntop.nodes[0], '__len__') else len(ntop.nodes)
    n_bot_count = len(nbot.nodes[0]) if hasattr(nbot.nodes[0], '__len__') else len(nbot.nodes)
    print("N_TOP nodes: %d, N_BOTTOM nodes: %d" % (n_top_count, n_bot_count))

    # Node coordinates map: label -> (x, y)
    t_mesh = time.time()
    print("Building node coordinate map...")
    node_coords = {}
    for n in inst.nodes:
        node_coords[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))

    # Element centroids map: label -> (x_c, y_c)
    print("Building element centroid map...")
    elem_centroids = {}
    for el in inst.elements:
        conn = el.connectivity
        xs = [node_coords[nl][0] for nl in conn if nl in node_coords]
        ys = [node_coords[nl][1] for nl in conn if nl in node_coords]
        if xs and ys:
            elem_centroids[el.label] = (sum(xs) / float(len(xs)), sum(ys) / float(len(ys)))
    print("Mesh map built in %.2fs: %d nodes, %d elements" % (time.time() - t_mesh, len(node_coords), len(elem_centroids)))

    # Extract complete U-RF curve across all steps
    step_names = list(odb.steps.keys())
    print("Steps: %s" % step_names)
    
    curve_data = []
    all_frames_ref = []
    global_frame_counter = 0

    for s_name in step_names:
        step = odb.steps[s_name]
        n_frames = len(step.frames)
        print("  Scanning Step '%s': %d frames..." % (s_name, n_frames))
        for f_idx, frame in enumerate(step.frames):
            u_rp = 0.0
            rf_rp = 0.0
            if 'U' in frame.fieldOutputs:
                for v in frame.fieldOutputs['U'].values:
                    if v.nodeLabel == 999999:
                        u_rp = float(v.data[1])
                        break
            if 'RF' in frame.fieldOutputs:
                for v in frame.fieldOutputs['RF'].values:
                    if v.nodeLabel == 999999:
                        rf_rp = float(v.data[1])
                        break

            curve_data.append({
                'global_frame_idx': global_frame_counter,
                'step_name': s_name,
                'step_frame_idx': f_idx,
                'step_time': float(frame.frameValue),
                'u_mm': u_rp,
                'rf_kN': rf_rp
            })
            all_frames_ref.append((s_name, f_idx, frame))
            global_frame_counter += 1

    # Extract raw arrays
    u_raw = [pt['u_mm'] for pt in curve_data]
    rf_raw = [pt['rf_kN'] for pt in curve_data]
    curve_hash = compute_array_sha256(u_raw, rf_raw)

    if out_csv_path:
        with open(out_csv_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['displacement_mm', 'reaction_force_kN', 'step_name', 'step_frame_idx'])
            for pt in curve_data:
                writer.writerow(["%.10e" % pt['u_mm'], "%.10e" % pt['rf_kN'], pt['step_name'], pt['step_frame_idx']])
        print("Exported F-u curve to: %s" % out_csv_path)

    # Checkpoint damage field extraction
    raw_checkpoints = [0.0050, 0.0055, 0.00575, 0.0060, 0.006200]
    u_terminal = u_raw[-1] if u_raw else 0.0
    
    checkpoints = []
    for cp in raw_checkpoints:
        if cp <= u_terminal + 1e-6:
            checkpoints.append(cp)

    checkpoint_results = {}
    print("\nExtracting spatial damage field SDV14 at checkpoints...")
    for cp in checkpoints:
        best_pt = min(curve_data, key=lambda pt: abs(pt['u_mm'] - cp))
        g_idx = best_pt['global_frame_idx']
        s_name, f_idx, frame = all_frames_ref[g_idx]
        actual_u = best_pt['u_mm']
        actual_rf = best_pt['rf_kN']

        t_cp = time.time()
        d_spatial = []
        if 'SDV14' in frame.fieldOutputs:
            sdv14_fo = frame.fieldOutputs['SDV14']
            for v in sdv14_fo.values:
                el_label = v.elementLabel
                if el_label in elem_centroids:
                    xc, yc = elem_centroids[el_label]
                    d_spatial.append((xc, yc, float(v.data)))
        elif 'SDV' in frame.fieldOutputs:
            sdv_fo = frame.fieldOutputs['SDV']
            for v in sdv_fo.values:
                el_label = v.elementLabel
                if el_label in elem_centroids:
                    xc, yc = elem_centroids[el_label]
                    if hasattr(v.data, '__len__') and len(v.data) >= 14:
                        d_spatial.append((xc, yc, float(v.data[13])))
                    elif not hasattr(v.data, '__len__'):
                        d_spatial.append((xc, yc, float(v.data)))

        d_vals = [p[2] for p in d_spatial] if d_spatial else [0.0]
        d_min = min(d_vals)
        d_max = max(d_vals)

        if d_min >= -1e-5 and d_max <= 1.00001:
            bounds_status = 'BOUND_STRICT_PASS'
            bounds_valid = True
        elif d_min >= -1e-5 and d_max <= 1.005:
            bounds_status = 'SMALL_BOUND_OVERSHOOT_OBSERVED'
            bounds_valid = True
        else:
            bounds_status = 'BOUNDS_VIOLATION'
            bounds_valid = False

        # Crack tip damage at (0.50, 0.50)
        tip_pts = []
        for x, y, d_val in d_spatial:
            dist = math.sqrt((x - 0.5)**2 + (y - 0.5)**2)
            if dist <= 0.020:
                tip_pts.append((x, y, d_val, dist))
        tip_pts.sort(key=lambda t: t[3])
        tip_d = tip_pts[0][2] if tip_pts else 0.0

        # Horizontal profile along y = 0.50 mm (+/- 0.005 mm)
        horiz_profile = []
        for x, y, d_val in d_spatial:
            if abs(y - 0.50) <= 0.005 and x >= 0.40:
                horiz_profile.append((round(x, 6), round(d_val, 6)))
        horiz_profile.sort(key=lambda p: p[0])

        # Transverse profile at x = 0.55 mm (+/- 0.005 mm)
        trans_profile_55 = []
        for x, y, d_val in d_spatial:
            if abs(x - 0.55) <= 0.005 and 0.45 <= y <= 0.55:
                trans_profile_55.append((round(y, 6), round(d_val, 6)))
        trans_profile_55.sort(key=lambda p: p[0])

        # Crack ridge calculation: group by x bins of 0.005 mm for x >= 0.50 mm where d >= 0.30
        bins = {}
        for x, y, d_val in d_spatial:
            if x >= 0.50 and d_val >= 0.30:
                x_bin = round(round(x / 0.005) * 0.005, 4)
                if x_bin not in bins or d_val > bins[x_bin]['d']:
                    bins[x_bin] = {'x': x, 'y': y, 'd': d_val}

        ridge_pts = sorted(bins.values(), key=lambda b: b['x'])
        deviations = [abs(p['y'] - 0.50) for p in ridge_pts]
        max_dev = max(deviations) if deviations else 0.0
        mean_dev = (sum(deviations) / float(len(deviations))) if deviations else 0.0

        # Crack tip contour (d = 0.90)
        tip_09_x = None
        for p in ridge_pts:
            if p['d'] >= 0.90:
                tip_09_x = p['x']

        checkpoint_results["%.6f" % cp] = {
            'target_u_mm': cp,
            'actual_u_mm': actual_u,
            'actual_rf_kN': actual_rf,
            'step_name': s_name,
            'step_frame_idx': f_idx,
            'global_frame_idx': g_idx,
            'status': bounds_status,
            'd_min': float(d_min),
            'd_max': float(d_max),
            'bounds_valid': bounds_valid,
            'crack_tip_d': float(tip_d),
            'tip_d09_front_x_mm': float(tip_09_x) if tip_09_x is not None else None,
            'horizontal_profile_points': len(horiz_profile),
            'horizontal_profile_sample': horiz_profile[::max(1, len(horiz_profile)//10)],
            'transverse_profile_55_sample': trans_profile_55[::max(1, len(trans_profile_55)//10)],
            'ridge_points_count': len(ridge_pts),
            'ridge_points': [{'x': round(p['x'], 6), 'y': round(p['y'], 6), 'd': round(p['d'], 6)} for p in ridge_pts],
            'max_path_deviation_y_mm': float(max_dev),
            'mean_path_deviation_y_mm': float(mean_dev)
        }
        print("  Checkpoint u=%.6f mm (Step %s, Frame %d): d_min=%.6f, d_max=%.6f [%s], tip_d=%.6f, max_dev=%.6f mm (in %.2fs)" %
              (cp, s_name, f_idx, d_min, d_max, bounds_status, tip_d, max_dev, time.time() - t_cp))

    odb.close()
    return {
        'total_nodes': len(node_coords),
        'total_elements': len(elem_centroids),
        'n_top_count': n_top_count,
        'n_bottom_count': n_bot_count,
        'curve_points_count': len(u_raw),
        'curve_sha256': curve_hash,
        'u_raw': u_raw,
        'rf_raw': rf_raw,
        'checkpoints': checkpoint_results
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--odb', default='PK_M1_NOM1_STRICT_0062.odb')
    parser.add_argument('--sta', default='PK_M1_NOM1_STRICT_0062.sta')
    parser.add_argument('--base-csv', default='/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/83_gate6_adaptive_nominal_1pct_field_qualification/curve_1404454_field_qual.csv')
    parser.add_argument('--out-json', default='gate6_1404933_authoritative_evaluation.json')
    parser.add_argument('--out-csv', default='curve_1404933_extracted.csv')
    args = parser.parse_args()

    t_start = time.time()
    print("================================================================================")
    print("AUTHORITATIVE TERMINAL EVALUATION: JOB 1404933.mmaster02 (PK_M1_NOM1_STRICT_0062)")
    print("================================================================================")

    # 1. Extraction from ODB
    odb_res = extract_from_odb(args.odb, out_csv_path=args.out_csv)
    u_cand = odb_res['u_raw']
    f_cand = odb_res['rf_raw']

    # 2. Canonical K0 linear fit on 0 < u <= 0.001000 mm
    fit_u = []
    fit_f = []
    for u, f in zip(u_cand, f_cand):
        if 1e-8 < u <= 0.0010000001:
            fit_u.append(u)
            fit_f.append(f)

    k0_slope, k0_intercept, k0_r2 = linear_regression_ols(fit_u, fit_f)
    ref_k0 = 137.945520
    prod_k0 = 137.820804
    delta_k0_ref_pct = ((k0_slope - ref_k0) / ref_k0) * 100.0
    delta_k0_prod_pct = ((k0_slope - prod_k0) / prod_k0) * 100.0

    # 3. Peak force and displacement
    f_max = max(f_cand) if f_cand else 0.0
    idx_peak = f_cand.index(f_max) if f_cand else 0
    u_peak = u_cand[idx_peak] if u_cand else 0.0

    # Total external work on entire curve
    w_ext_mJ = trapezoidal_work(u_cand, f_cand) * 1000.0

    # 4. Pairwise comparison against Baseline Job 1404454
    comp_base = {}
    if args.base_csv and os.path.exists(args.base_csv):
        print("\nLoading baseline Job 1404454 curve: %s" % args.base_csv)
        u_base, f_base = load_csv_curve(args.base_csv)
        u_common_max = min(u_cand[-1], u_base[-1])
        
        # Candidate points on common interval
        u_c = [u for u in u_cand if u <= u_common_max + 1e-12]
        f_c = [f for u, f in zip(u_cand, f_cand) if u <= u_common_max + 1e-12]
        
        # Interpolate baseline at candidate points
        f_b_interp = interp_1d(u_c, u_base, f_base)
        diffs = [fc - fb for fc, fb in zip(f_c, f_b_interp)]
        abs_diffs = [abs(d) for d in diffs]
        
        max_abs_diff_kN = max(abs_diffs) if abs_diffs else 0.0
        mean_abs_diff_kN = sum(abs_diffs) / len(abs_diffs) if abs_diffs else 0.0
        
        sq_diffs = [d ** 2 for d in diffs]
        discrete_rms_kN = math.sqrt(sum(sq_diffs) / len(sq_diffs)) if sq_diffs else 0.0
        
        l2_integral = 0.0
        for i in range(len(u_c) - 1):
            du = u_c[i+1] - u_c[i]
            avg_sq = 0.5 * (sq_diffs[i+1] + sq_diffs[i])
            l2_integral += avg_sq * du
        continuous_l2_kN = math.sqrt(l2_integral / u_common_max) if u_common_max > 0.0 else 0.0

        crossings = {'1N': None, '5N': None, '10N': None}
        for u, ad in zip(u_c, abs_diffs):
            if crossings['1N'] is None and ad >= 0.0010:
                crossings['1N'] = float(u)
            if crossings['5N'] is None and ad >= 0.0050:
                crossings['5N'] = float(u)
            if crossings['10N'] is None and ad >= 0.0100:
                crossings['10N'] = float(u)

        w_cand_common = trapezoidal_work(u_c, f_c) * 1000.0
        w_base_common = trapezoidal_work(u_c, f_b_interp) * 1000.0
        delta_w_pct = ((w_cand_common - w_base_common) / w_base_common) * 100.0 if w_base_common > 0.0 else 0.0

        comp_base = {
            'baseline_source': args.base_csv,
            'common_u_max_mm': float(u_common_max),
            'points_evaluated': len(u_c),
            'max_abs_diff_kN': float(max_abs_diff_kN),
            'max_abs_diff_N': float(max_abs_diff_kN * 1000.0),
            'mean_abs_diff_kN': float(mean_abs_diff_kN),
            'mean_abs_diff_N': float(mean_abs_diff_kN * 1000.0),
            'discrete_rms_kN': float(discrete_rms_kN),
            'discrete_rms_N': float(discrete_rms_kN * 1000.0),
            'continuous_l2_kN': float(continuous_l2_kN),
            'continuous_l2_N': float(continuous_l2_kN * 1000.0),
            'crossings_mm': crossings,
            'w_cand_common_mJ': float(w_cand_common),
            'w_base_common_mJ': float(w_base_common),
            'delta_w_pct': float(delta_w_pct),
            'mechanical_neutrality_pass': bool(discrete_rms_kN * 1000.0 < 5.0 and abs(delta_k0_prod_pct) < 0.01)
        }

    # 5. Solver telemetry
    sta_data = parse_sta_file(args.sta)

    # 6. Assemble complete report
    summary = {
        'job_id': '1404933.mmaster02',
        'job_name': 'PK_M1_NOM1_STRICT_0062',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'execution_walltime_seconds': round(time.time() - t_start, 2),
        'boundary_sets_verification': {
            'n_top_count': odb_res['n_top_count'],
            'n_top_expected': 210,
            'n_top_pass': odb_res['n_top_count'] == 210,
            'n_bottom_count': odb_res['n_bottom_count'],
            'n_bottom_expected': 150,
            'n_bottom_pass': odb_res['n_bottom_count'] == 150
        },
        'curve_hash': odb_res['curve_sha256'],
        'canonical_k0': {
            'k0_slope_kN_per_mm': k0_slope,
            'k0_intercept_kN': k0_intercept,
            'k0_r2': k0_r2,
            'sample_count_N': len(fit_u),
            'fit_interval_u_mm': [fit_u[0] if fit_u else 0.0, fit_u[-1] if fit_u else 0.0],
            'delta_k0_vs_ref_1398090_pct': delta_k0_ref_pct,
            'delta_k0_vs_prod_1404454_pct': delta_k0_prod_pct
        },
        'peak_metrics': {
            'f_max_kN': f_max,
            'u_peak_mm': u_peak,
            'delta_f_max_vs_prod_1404454_pct': ((f_max - 0.745325) / 0.745325) * 100.0,
            'delta_u_peak_vs_prod_1404454_pct': ((u_peak - 0.00575) / 0.00575) * 100.0
        },
        'trajectory_endpoints': {
            'u_terminal_mm': u_cand[-1] if u_cand else 0.0,
            'rf_terminal_kN': f_cand[-1] if f_cand else 0.0,
            'total_converged_points': len(u_cand)
        },
        'fracture_work': {
            'w_ext_mJ': w_ext_mJ
        },
        'pairwise_comparison_vs_baseline_1404454': comp_base,
        'solver_telemetry': sta_data,
        'damage_field_checkpoints': odb_res['checkpoints']
    }

    with open(args.out_json, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "="*80)
    print("AUTHORITATIVE SUMMARY: JOB 1404933.mmaster02")
    print("="*80)
    print("Boundary Sets: N_TOP=%d (expected 210), N_BOTTOM=%d (expected 150)" % (odb_res['n_top_count'], odb_res['n_bottom_count']))
    print("Canonical K0: %.6f kN/mm (R^2 = %.8f, N = %d)" % (k0_slope, k0_r2, len(fit_u)))
    print("  Delta K0 vs Reference 1398090 (137.945520 kN/mm): %+.4f%%" % delta_k0_ref_pct)
    print("  Delta K0 vs Production 1404454 (137.820804 kN/mm): %+.4f%%" % delta_k0_prod_pct)
    print("Peak Force: F_max = %.6f kN at u = %.6f mm" % (f_max, u_peak))
    print("Terminal State: u = %.6f mm, RF = %.6f kN" % (summary['trajectory_endpoints']['u_terminal_mm'], summary['trajectory_endpoints']['rf_terminal_kN']))
    print("External Work: W_ext = %.6f mJ" % w_ext_mJ)
    if comp_base:
        print("\nPairwise Parity vs Baseline 1404454 (Mechanical Neutrality Check):")
        print("  Common interval: 0 to %.6f mm (%d points)" % (comp_base['common_u_max_mm'], comp_base['points_evaluated']))
        print("  Max absolute diff: %.4f N (%.6f kN)" % (comp_base['max_abs_diff_N'], comp_base['max_abs_diff_kN']))
        print("  Discrete RMS: %.4f N, Continuous L2: %.4f N" % (comp_base['discrete_rms_N'], comp_base['continuous_l2_N']))
        print("  Divergence Crossings: 1N=%s mm, 5N=%s mm, 10N=%s mm" % (comp_base['crossings_mm']['1N'], comp_base['crossings_mm']['5N'], comp_base['crossings_mm']['10N']))
        print("  Delta W_ext on common interval: %+.4f%%" % comp_base['delta_w_pct'])
        print("  Mechanical Neutrality Status: %s" % ("PASS" if comp_base['mechanical_neutrality_pass'] else "INVESTIGATE"))
    print("="*80)
    print("Saved authoritative evaluation JSON to: %s" % args.out_json)

if __name__ == '__main__':
    main()
