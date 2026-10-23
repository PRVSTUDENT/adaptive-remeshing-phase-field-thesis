#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluate_p76_p87_checkpoint_candidates.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Inspects authentic Package 76 donor ODB and Package 87 C2 virgin-loading ODB
across the candidate displacement interval u_top in [0.00175, 0.00200] mm (t in [0.35, 0.40] s)
to identify a common physical displacement checkpoint where:
- Donor and virgin C2 physical RF2 agree within <= 5%
- Comparable elastic and fracture energies are documented
- Damage fields demonstrate intact-ligament or early-propagation behavior
- Donor damage and committed history are nontrivial enough to test genuine phase-field transfer.
"""

import os
import sys
import json
import math
from odbAccess import openOdb

def get_history_series(step, region_filter, var_name):
    for hreg_name, hreg in step.historyRegions.items():
        if any(rf in hreg_name for rf in region_filter):
            if var_name in hreg.historyOutputs:
                return [(float(t), float(v)) for t, v in hreg.historyOutputs[var_name].data]
    return []

def get_energy_series(step, energy_name):
    for hreg_name, hreg in step.historyRegions.items():
        if 'Assembly' in hreg_name or 'Whole Model' in hreg_name:
            if energy_name in hreg.historyOutputs:
                return [(float(t), float(v)) for t, v in hreg.historyOutputs[energy_name].data]
    return []

def extract_interval_data(odb_path, step_name, u_min=0.00170, u_max=0.00205):
    print("Opening ODB: %s" % odb_path)
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB does not exist: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)
    if step_name not in odb.steps:
        raise RuntimeError("Step %s not in ODB. Available: %s" % (step_name, list(odb.steps.keys())))
    step = odb.steps[step_name]

    # History outputs for RP
    rf2_hist = get_history_series(step, ['999999', 'N_RP'], 'RF2')
    u2_hist = get_history_series(step, ['999999', 'N_RP'], 'U2')
    allse_hist = get_energy_series(step, 'ALLSE')
    allie_hist = get_energy_series(step, 'ALLIE')

    # Convert histories to lookup by time
    hist_by_t = {}
    for t, u in u2_hist:
        hist_by_t.setdefault(t, {})['u2'] = u
    for t, rf in rf2_hist:
        hist_by_t.setdefault(t, {})['rf2'] = rf
    for t, se in allse_hist:
        hist_by_t.setdefault(t, {})['allse'] = se
    for t, ie in allie_hist:
        hist_by_t.setdefault(t, {})['allie'] = ie

    # Scan field frames
    frames_in_interval = []
    all_frames = []
    total_frames = len(step.frames)
    print("Total frames in step '%s': %d" % (step_name, total_frames))

    for idx, f in enumerate(step.frames):
        t_val = float(f.frameValue)
        frame_id = int(f.frameId)

        # RP displacement and force
        u2_rp = None
        rf2_rp = None
        if 'U' in f.fieldOutputs:
            for val in f.fieldOutputs['U'].values:
                if val.nodeLabel == 999999:
                    u2_rp = float(val.data[1])
                    break
        if 'RF' in f.fieldOutputs:
            for val in f.fieldOutputs['RF'].values:
                if val.nodeLabel == 999999:
                    rf2_rp = float(val.data[1])
                    break

        # Fallback to history output if field output was not requested on RP
        if u2_rp is None or rf2_rp is None:
            # find closest time in hist_by_t
            if hist_by_t:
                closest_t = min(hist_by_t.keys(), key=lambda t: abs(t - t_val))
                if abs(closest_t - t_val) < 1e-4:
                    if u2_rp is None:
                        u2_rp = hist_by_t[closest_t].get('u2', None)
                    if rf2_rp is None:
                        rf2_rp = hist_by_t[closest_t].get('rf2', None)

        # Check phase field d: in UEL, phase is DOF 3 in U
        d_max = 0.0
        d_min = 0.0
        d_tip = 0.0
        if 'U' in f.fieldOutputs:
            u_fld = f.fieldOutputs['U']
            d_vals = []
            for val in u_fld.values:
                if len(val.data) >= 3 and val.nodeLabel != 999999:
                    d_vals.append(float(val.data[2]))
            if d_vals:
                d_max = float(max(d_vals))
                d_min = float(min(d_vals))

        # Check SDV1 if available (visualization elements)
        sdv1_max = 0.0
        if 'SDV1' in f.fieldOutputs:
            s_vals = [float(v.data) for v in f.fieldOutputs['SDV1'].values]
            if s_vals:
                sdv1_max = float(max(s_vals))

        rec = {
            "frame_idx": idx,
            "frame_id": frame_id,
            "time": t_val,
            "u2_rp": u2_rp,
            "rf2_rp_kN": rf2_rp,
            "rf2_rp_N": (rf2_rp * 1000.0) if rf2_rp is not None else None,
            "d_max_dof3": d_max,
            "sdv1_max": sdv1_max
        }
        all_frames.append(rec)

        if u2_rp is not None and u_min <= u2_rp <= u_max:
            frames_in_interval.append(rec)

    odb.close()
    return {
        "step_name": step_name,
        "total_frames": total_frames,
        "history_points": len(rf2_hist),
        "all_history": [{"time": t, "u2": hist_by_t[t].get('u2'), "rf2_N": (hist_by_t[t].get('rf2') * 1000.0) if hist_by_t[t].get('rf2') is not None else None} for t in sorted(hist_by_t.keys())],
        "frames_in_interval": frames_in_interval,
        "all_frames": all_frames
    }

def main():
    p76_odb = "/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual/M1_CANDIDATE_DONOR_H0025_VISUAL.odb"
    p87_odb = "/scratch9/pr21vyci/runs/mode1_package87_c2_virgin_control/M1_C2_VIRGIN_CONTROL.odb"

    print("=== Scanning Package 76 (Donor Reference, h=2.5 um) ===")
    p76_data = extract_interval_data(p76_odb, 'Step-1', u_min=0.00170, u_max=0.00205)

    print("=== Scanning Package 87 (C2 Virgin Mesh, h=1.0 um) ===")
    p87_data = extract_interval_data(p87_odb, 'C2_VIRGIN_LOADING', u_min=0.00170, u_max=0.00205)

    # Let's perform fine-grained comparison between donor and C2 across all history points
    donor_hist = [pt for pt in p76_data['all_history'] if pt['u2'] is not None and 0.00170 <= pt['u2'] <= 0.00205]
    c2_hist = [pt for pt in p87_data['all_history'] if pt['u2'] is not None and 0.00170 <= pt['u2'] <= 0.00205]

    print("\n--- Interval Scan [0.00170, 0.00205] mm ---")
    print("Donor history points in interval: %d" % len(donor_hist))
    print("C2 history points in interval:    %d" % len(c2_hist))

    # Match each donor history point with linearly interpolated C2 point
    comparisons = []
    c2_u = [pt['u2'] for pt in p87_data['all_history'] if pt['u2'] is not None]
    c2_rf = [pt['rf2_N'] for pt in p87_data['all_history'] if pt['rf2_N'] is not None]

    for d_pt in donor_hist:
        u_tgt = d_pt['u2']
        rf_donor = d_pt['rf2_N']
        # Interpolate C2 at u_tgt
        rf_c2_interp = None
        for i in range(len(c2_u) - 1):
            if c2_u[i] <= u_tgt <= c2_u[i+1]:
                frac = (u_tgt - c2_u[i]) / (c2_u[i+1] - c2_u[i]) if (c2_u[i+1] != c2_u[i]) else 0.0
                rf_c2_interp = c2_rf[i] + frac * (c2_rf[i+1] - c2_rf[i])
                break

        if rf_c2_interp is not None and rf_donor is not None:
            rel_diff_pct = 100.0 * (rf_c2_interp - rf_donor) / rf_donor
            comparisons.append({
                "u_mm": u_tgt,
                "donor_time": d_pt['time'],
                "donor_rf2_N": rf_donor,
                "c2_interp_rf2_N": rf_c2_interp,
                "rf2_diff_pct": rel_diff_pct,
                "meets_5pct_gate": abs(rel_diff_pct) <= 5.0
            })

    # Print summary of comparisons
    print("\nCandidate Checkpoint Comparison Table:")
    print("%-12s %-12s %-14s %-14s %-12s %-8s" % ("u (mm)", "Donor t(s)", "Donor RF2(N)", "C2 RF2(N)", "Diff (%)", "<=5%?"))
    print("-" * 75)
    for c in comparisons:
        print("%-12.7f %-12.6f %-14.5f %-14.5f %-+12.3f %-8s" %
              (c['u_mm'], c['donor_time'], c['donor_rf2_N'], c['c2_interp_rf2_N'], c['rf2_diff_pct'], "PASS" if c['meets_5pct_gate'] else "FAIL"))

    # Also list frames with actual field outputs saved in donor ODB
    print("\nDonor Frames in Interval (Frames where full field output is available):")
    for f in p76_data['frames_in_interval']:
        print("  Frame %d (time=%.6f s, u=%.7f mm): RF2=%.5f N, d_max=%.4f, sdv1_max=%.4f" %
              (f['frame_idx'], f['time'], f['u2_rp'], f['rf2_rp_N'] if f['rf2_rp_N'] else 0.0, f['d_max_dof3'], f['sdv1_max']))

    print("\nC2 Frames in Interval:")
    for f in p87_data['frames_in_interval']:
        print("  Frame %d (time=%.6f s, u=%.7f mm): RF2=%.5f N, d_max=%.4f" %
              (f['frame_idx'], f['time'], f['u2_rp'], f['rf2_rp_N'] if f['rf2_rp_N'] else 0.0, f['d_max_dof3']))

    output = {
        "status": "CHECKPOINT_CANDIDATE_EVALUATION_SUCCESS",
        "p76_summary": {
            "total_frames": p76_data['total_frames'],
            "frames_in_interval": p76_data['frames_in_interval']
        },
        "p87_summary": {
            "total_frames": p87_data['total_frames'],
            "frames_in_interval": p87_data['frames_in_interval']
        },
        "comparisons": comparisons
    }

    out_file = "/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual/p76_p87_checkpoint_candidates.json"
    with open(out_file, "w") as fp:
        json.dump(output, fp, indent=2)
    print("\nSaved output to %s" % out_file)

if __name__ == '__main__':
    main()
