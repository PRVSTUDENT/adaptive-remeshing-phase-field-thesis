# -*- coding: utf-8 -*-
"""
extract_mode2_paper_horizon_terminal_evidence.py

Abaqus Python (Python 2.7 / odbAccess) extractor for Job-1_UEL_paper_horizon.odb.
Extracts:
1. Complete reaction force vs displacement (Fx - ux) history from Node N_RP.
2. Complete maximum damage (d_max) history across all steps and frames.
3. Raw element-wise MISESERI and SDV damage fields at target displacement states:
   ux = {0.00936, 0.01000, 0.011842, 0.01626, 0.02000} mm.
4. Comprehensive provenance and geometric corridor metrics.

Governing Reference: Pandey & Kumar (2025) Section 4.2, Figs. 6(b), 12, 13(a).
"""

from __future__ import print_function
import os
import sys
import math
import json
import odbAccess

# Target physical displacements (in mm)
TARGET_UX_LIST = [0.00936, 0.01000, 0.011842, 0.01626, 0.02000]

# Digitized Fig. 6(b) reference trajectory points
DIGITIZED_FIG6B = [
    (0.495, 0.514), (0.540, 0.460), (0.600, 0.380),
    (0.680, 0.280), (0.760, 0.180), (0.840, 0.080), (0.930, 0.000)
]

def extract_terminal_evidence(odb_path="Job-1_UEL_paper_horizon.odb", out_dir="."):
    if not os.path.exists(odb_path):
        print("[ERROR] ODB file not found: %s" % odb_path)
        sys.exit(1)

    print("=" * 75)
    print("MODE-II GATE M2-2 TERMINAL EVIDENCE EXTRACTION")
    print("ODB: %s" % odb_path)
    print("=" * 75)

    o = odbAccess.openOdb(odb_path, readOnly=True)

    # 1. Inspect Steps and Mesh
    step_names = list(o.steps.keys())
    print("Available Steps: %s" % step_names)

    inst_name = list(o.rootAssembly.instances.keys())[0]
    inst = o.rootAssembly.instances[inst_name]
    nodes = {n.label: n.coordinates for n in inst.nodes}
    elements = {e.label: e.connectivity for e in inst.elements}
    total_elements = len(elements)
    n_phys = total_elements // 3 if total_elements > 3000 else 2960

    print("Mesh: Total Elements=%d, Co-located Layers=3, Underlying FEs=%d, Nodes=%d" % 
          (total_elements, n_phys, len(nodes)))

    # Compute element centroids
    centroids = {}
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if pts:
            xc = sum(p[0] for p in pts) / float(len(pts))
            yc = sum(p[1] for p in pts) / float(len(pts))
            centroids[eid] = (xc, yc)
        else:
            centroids[eid] = (0.0, 0.0)

    # 2. Extract Reaction Force vs Displacement History
    rf_history = []
    dmax_history = []
    all_frames_index = []

    cumulative_u = 0.0

    for s_idx, s_name in enumerate(step_names):
        step = o.steps[s_name]
        step_frames = step.frames
        print("Processing Step '%s' (%d frames)..." % (s_name, len(step_frames)))

        for f_idx, f in enumerate(step_frames):
            f_id = int(f.frameId)
            f_val = float(f.frameValue)
            inc_num = int(f.incrementNumber) if hasattr(f, 'incrementNumber') else f_idx

            # Physical displacement calculation
            if s_name == "Step-1":
                current_ux = f_val * 0.0100
            elif s_name == "Step-2":
                current_ux = 0.0100 + f_val * 0.0100
            else:
                current_ux = f_val

            # RF and U extraction at N_RP
            rf_x = 0.0
            ux_actual = current_ux
            if 'RF' in f.fieldOutputs:
                fo_rf = f.fieldOutputs['RF']
                for val in fo_rf.values:
                    if val.nodeLabel == 999999 or val.nodeLabel == 1:
                        rf_x = float(val.data[0]) if hasattr(val.data, '__getitem__') else float(val.data)
                        break
            if 'U' in f.fieldOutputs:
                fo_u = f.fieldOutputs['U']
                for val in fo_u.values:
                    if val.nodeLabel == 999999 or val.nodeLabel == 1:
                        ux_actual = float(val.data[0]) if hasattr(val.data, '__getitem__') else float(val.data)
                        break

            # Extract d_max from SDV1
            d_max_val = 0.0
            if 'SDV_SDV1' in f.fieldOutputs:
                fo_sdv1 = f.fieldOutputs['SDV_SDV1']
                vals = [float(v.data) for v in fo_sdv1.values]
                if vals:
                    d_max_val = max(vals)
            elif 'SDV1' in f.fieldOutputs:
                fo_sdv1 = f.fieldOutputs['SDV1']
                vals = [float(v.data) for v in fo_sdv1.values]
                if vals:
                    d_max_val = max(vals)

            rf_history.append({
                'step_name': s_name,
                'frame_id': f_id,
                'increment': inc_num,
                'step_time': f_val,
                'ux_nominal_mm': current_ux,
                'ux_actual_mm': ux_actual,
                'fx_kN': rf_x
            })

            dmax_history.append({
                'step_name': s_name,
                'frame_id': f_id,
                'increment': inc_num,
                'step_time': f_val,
                'ux_mm': current_ux,
                'd_max': d_max_val
            })

            all_frames_index.append({
                'step_name': s_name,
                'step_index': s_idx,
                'frame_index': f_idx,
                'frame_id': f_id,
                'increment': inc_num,
                'step_time': f_val,
                'ux_mm': current_ux,
                'frame_obj': f
            })

    # Save RF history CSV
    rf_csv_path = os.path.join(out_dir, "mode2_j1_rf_history.csv")
    with open(rf_csv_path, "w") as f:
        f.write("step_name,frame_id,increment,step_time,ux_nominal_mm,ux_actual_mm,fx_kN\n")
        for r in rf_history:
            f.write("%s,%d,%d,%.6f,%.8e,%.8e,%.8e\n" % 
                    (r['step_name'], r['frame_id'], r['increment'], r['step_time'], r['ux_nominal_mm'], r['ux_actual_mm'], r['fx_kN']))
    print("Saved RF history: %s (%d points)" % (rf_csv_path, len(rf_history)))

    # Save d_max history CSV
    dmax_csv_path = os.path.join(out_dir, "mode2_j1_dmax_history.csv")
    with open(dmax_csv_path, "w") as f:
        f.write("step_name,frame_id,increment,step_time,ux_mm,d_max\n")
        for r in dmax_history:
            f.write("%s,%d,%d,%.6f,%.8e,%.8e\n" % 
                    (r['step_name'], r['frame_id'], r['increment'], r['step_time'], r['ux_mm'], r['d_max']))
    print("Saved d_max history: %s (%d points)" % (dmax_csv_path, len(dmax_history)))

    # 3. Extract Snapshots at Target Displacements
    snapshots_meta = []

    for target_u in TARGET_UX_LIST:
        # Find nearest frame
        best_frame = min(all_frames_index, key=lambda item: abs(item['ux_mm'] - target_u))
        f = best_frame['frame_obj']
        s_name = best_frame['step_name']
        f_id = best_frame['frame_id']
        inc_num = best_frame['increment']
        actual_u = best_frame['ux_mm']
        u_error_nm = abs(actual_u - target_u) * 1e6

        print("\n--- Target ux = %.5f mm: Nearest Frame %d in '%s' (ux = %.5f mm, delta = %.1f nm) ---" % 
              (target_u, f_id, s_name, actual_u, u_error_nm))

        # Extract MISESERI field
        miseseri_records = []
        if 'MISESERI' in f.fieldOutputs:
            fo_miseseri = f.fieldOutputs['MISESERI']
            for val in fo_miseseri.values:
                eid = val.elementLabel
                m_val = float(val.data)
                base_eid = eid - 2 * n_phys if eid > 2 * n_phys else (eid - n_phys if eid > n_phys else eid)
                xc, yc = centroids.get(eid, centroids.get(base_eid, (0.0, 0.0)))
                miseseri_records.append({
                    'eid': eid,
                    'base_eid': base_eid,
                    'xc': xc,
                    'yc': yc,
                    'miseseri': m_val
                })

        # Extract Damage SDV1 field
        damage_records = []
        sdv_field_name = 'SDV_SDV1' if 'SDV_SDV1' in f.fieldOutputs else ('SDV1' if 'SDV1' in f.fieldOutputs else None)
        if sdv_field_name and sdv_field_name in f.fieldOutputs:
            fo_sdv = f.fieldOutputs[sdv_field_name]
            for val in fo_sdv.values:
                eid = val.elementLabel
                d_val = float(val.data)
                base_eid = eid - n_phys if eid > n_phys else eid
                xc, yc = centroids.get(eid, centroids.get(base_eid, (0.0, 0.0)))
                damage_records.append({
                    'eid': eid,
                    'base_eid': base_eid,
                    'xc': xc,
                    'yc': yc,
                    'damage': d_val
                })

        # Save snapshot CSVs
        tag = ("%.5f" % target_u).replace('.', 'p')
        mises_csv = os.path.join(out_dir, "miseseri_snapshot_ux_%s.csv" % tag)
        with open(mises_csv, "w") as f_out:
            f_out.write("base_eid,layer3_eid,xc,yc,miseseri\n")
            for r in sorted(miseseri_records, key=lambda x: x['base_eid']):
                f_out.write("%d,%d,%.6f,%.6f,%.8e\n" % (r['base_eid'], r['eid'], r['xc'], r['yc'], r['miseseri']))

        damage_csv = os.path.join(out_dir, "damage_snapshot_ux_%s.csv" % tag)
        with open(damage_csv, "w") as f_out:
            f_out.write("base_eid,layer2_eid,xc,yc,damage\n")
            for r in sorted(damage_records, key=lambda x: x['base_eid']):
                f_out.write("%d,%d,%.6f,%.6f,%.8e\n" % (r['base_eid'], r['eid'], r['xc'], r['yc'], r['damage']))

        # Compute snapshot summary metrics
        max_miseseri = max([r['miseseri'] for r in miseseri_records]) if miseseri_records else 0.0
        mean_miseseri = sum([r['miseseri'] for r in miseseri_records]) / float(len(miseseri_records)) if miseseri_records else 0.0
        max_d = max([r['damage'] for r in damage_records]) if damage_records else 0.0

        # Corridor chord angle analysis
        corridor_elems = [r for r in miseseri_records if r['miseseri'] > 0.05 * max_miseseri and r['xc'] >= 0.45 and r['yc'] <= 0.55]
        centerline = []
        for y_val in [0.05 * i for i in range(11)]:
            band = [r for r in corridor_elems if abs(r['yc'] - y_val) <= 0.035]
            if band:
                mean_x = sum(r['xc'] for r in band) / float(len(band))
                centerline.append((mean_x, y_val))

        if len(centerline) >= 2:
            start_pt = max(centerline, key=lambda p: p[1])
            end_pt = min(centerline, key=lambda p: p[1])
            chord_angle = math.degrees(math.atan2(end_pt[1] - start_pt[1], end_pt[0] - start_pt[0]))
            exit_x = end_pt[0]
        else:
            chord_angle = 0.0
            exit_x = 0.5

        snapshots_meta.append({
            'target_ux_mm': target_u,
            'achieved_ux_mm': actual_u,
            'step_name': s_name,
            'frame_id': f_id,
            'increment': inc_num,
            'max_miseseri': max_miseseri,
            'mean_miseseri': mean_miseseri,
            'max_damage': max_d,
            'chord_angle_deg': chord_angle,
            'exit_x_at_y0': exit_x,
            'miseseri_csv': mises_csv,
            'damage_csv': damage_csv
        })

    o.close()

    # 4. Save Snapshots Manifest JSON
    manifest_path = os.path.join(out_dir, "MODE2_M2_2_TERMINAL_EXTRACTION_SUMMARY.json")
    with open(manifest_path, "w") as f:
        json.dump({
            'odb_path': odb_path,
            'total_steps': len(step_names),
            'step_names': step_names,
            'total_rf_points': len(rf_history),
            'snapshots': snapshots_meta,
            'fig6b_reference': {
                'chord_angle_deg': -49.74,
                'exit_x_mm': 0.930
            }
        }, f, indent=2)
    print("\nSaved full extraction summary: %s" % manifest_path)
    print("=" * 75)
    return manifest_path

if __name__ == "__main__":
    odb_arg = sys.argv[1] if len(sys.argv) >= 2 else "Job-1_UEL_paper_horizon.odb"
    out_arg = sys.argv[2] if len(sys.argv) >= 3 else "."
    extract_terminal_evidence(odb_arg, out_arg)
