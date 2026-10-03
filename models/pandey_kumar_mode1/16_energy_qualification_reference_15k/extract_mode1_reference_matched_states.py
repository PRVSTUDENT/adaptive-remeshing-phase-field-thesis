"""
Authoritative Matched-Displacement Reference Extraction Tool
Model: PK_MODE1_REF15K_ENERGY (Job 1409734.mmaster02, 15,192 finite elements)
Source ODB: /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/16_energy_qualification_reference_15k/PK_M1_REF15K_ENERGY.odb

Target Displacements (mm):
  u in {0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070, 0.0080, 0.0090, 0.0100}

Exports for each matched state:
  1. Reaction force F = +RF2 (kN) at RP Node 999999
  2. d_max (domain maximum phase field from SDV14)
  3. Crack-tip / right-ligament extent x_tip(d >= 0.90) and x_tip(d >= 0.95)
  4. Ligament profile d(x, y approx 0.5 mm)
  5. Full phase-field contour mapping for identical-axis plotting
  6. E_elas (mJ) from SDV18
  7. Implemented E_frac (mJ) from SDV17
  8. E_model = E_elas + E_frac (mJ)
  9. W_ext (mJ) via trapezoidal integration
 10. Delta_book = E_model - W_ext (mJ) and eps_book (%)
 11. Converged Step, Frame index, StepTime, TotalTime, Actual displacement

Outputs generated:
  - MODE1_REFERENCE_MATCHED_DISPLACEMENT_BUNDLE.json
  - mode1_reference_matched_states_summary.csv
  - mode1_reference_ligament_profiles.csv
  - mode1_reference_contour_matched_states.csv
"""

import sys
import os
import math
import json
import csv
from odbAccess import openOdb

TARGET_DISPLACEMENTS = [
    0.0010,
    0.0030,
    0.0050,
    0.005857,
    0.0060,
    0.0065,
    0.0070,
    0.0080,
    0.0090,
    0.0100
]

def extract_matched_reference_bundle(odb_path, out_dir):
    print("================================================================================")
    print("OPENING REFERENCE ODB: %s" % odb_path)
    print("================================================================================")
    odb = openOdb(odb_path, readOnly=True)
    
    # 1. First pass: compute complete F-u trajectory and cumulative external work
    print("\n--- Pass 1: Extracting full F-u trajectory for cumulative work integration ---")
    all_frames = []
    
    u_prev = 0.0
    rf_prev = 0.0
    w_cum = 0.0  # in kN*mm = J
    
    # Identify RP node set
    rp_set = None
    if 'N_RP' in odb.rootAssembly.nodeSets:
        rp_set = odb.rootAssembly.nodeSets['N_RP']
    elif 'SET_RP' in odb.rootAssembly.nodeSets:
        rp_set = odb.rootAssembly.nodeSets['SET_RP']

    global_frame_idx = 0
    for step_name in sorted(odb.steps.keys()):
        step = odb.steps[step_name]
        print("Scanning %s (%d frames)..." % (step_name, len(step.frames)))
        for frame_idx, frame in enumerate(step.frames):
            frame_val = float(frame.frameValue)
            
            # Displacement
            if step_name == 'Step-1':
                u_val = frame_val * 0.0050
                total_time = frame_val
            else:
                u_val = 0.0050 + frame_val * 0.0050
                total_time = 1.0 + frame_val
                
            # Reaction force at RP (tensile load is positive upward in RF2)
            rf_val = 0.0
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                if rp_set is not None:
                    rf_sub = rf_field.getSubset(region=rp_set)
                    for val in rf_sub.values:
                        rf_val = abs(float(val.data[1]))  # Tensile reaction force F > 0
                        break
                else:
                    for val in rf_field.values:
                        if val.nodeLabel == 999999 or val.nodeLabel == 1000000:
                            rf_val = abs(float(val.data[1]))
                            break

            # Trapezoidal work integration
            if global_frame_idx > 0:
                du = u_val - u_prev
                if du > 0:
                    dw = 0.5 * (rf_val + rf_prev) * du
                    w_cum += dw
            
            u_prev = u_val
            rf_prev = rf_val
            
            all_frames.append({
                'global_frame_idx': global_frame_idx,
                'step_name': step_name,
                'frame_idx': frame_idx,
                'step_time': frame_val,
                'total_time': total_time,
                'u_mm': u_val,
                'rf_kN': rf_val,
                'w_ext_kNmm': w_cum,
                'w_ext_mJ': w_cum * 1000.0
            })
            global_frame_idx += 1

    print("[INFO] Total trajectory frames indexed: %d" % len(all_frames))
    print("[INFO] Final external work: %.6f mJ" % (w_cum * 1000.0))

    # 2. Identify matched frames for target displacements
    print("\n--- Identifying Matched Frames for Target Displacements ---")
    matched_target_frames = []
    
    for u_target in TARGET_DISPLACEMENTS:
        best_frame = None
        min_diff = 1e9
        for f in all_frames:
            diff = abs(f['u_mm'] - u_target)
            if diff < min_diff:
                min_diff = diff
                best_frame = f
                
        print("Target u = %.6f mm -> Selected %s Frame %d (actual u = %.6f mm, diff = %.2e mm)" % 
              (u_target, best_frame['step_name'], best_frame['frame_idx'], best_frame['u_mm'], min_diff))
        matched_target_frames.append((u_target, best_frame))

    # 3. Extract detailed fields for each matched frame
    print("\n--- Pass 2: Extracting detailed energy, phase field, and ligament profiles ---")
    
    # Locate instances and sets
    instance_name = odb.rootAssembly.instances.keys()[0]
    instance = odb.rootAssembly.instances[instance_name]
    
    # Pre-index node coordinates
    node_coords = {}
    for node in instance.nodes:
        node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))
        
    print("[INFO] Indexed %d node coordinates in instance '%s'" % (len(node_coords), instance_name))

    # Pre-index element centroids
    elem_centroids = {}
    for elem in instance.elements:
        xs = [node_coords[nl][0] for nl in elem.connectivity]
        ys = [node_coords[nl][1] for nl in elem.connectivity]
        elem_centroids[elem.label] = (sum(xs)/float(len(xs)), sum(ys)/float(len(ys)))

    # Locate UMATELEM element set (Layer 3 companion elements)
    umatelem_set = None
    if 'UMATELEM' in odb.rootAssembly.elementSets:
        umatelem_set = odb.rootAssembly.elementSets['UMATELEM']
    elif 'UMATELEM' in instance.elementSets:
        umatelem_set = instance.elementSets['UMATELEM']

    # Filter companion elements
    if umatelem_set is not None:
        umatelem_labels = sorted(e.label for e in instance.elements if e in umatelem_set.elements[0])
    else:
        umatelem_labels = sorted(e.label for e in instance.elements if e.label > 30384)

    print("[INFO] Indexed %d companion elements in UMATELEM (labels %d to %d)" % 
          (len(umatelem_labels), umatelem_labels[0], umatelem_labels[-1]))

    # Pre-index ligament elements near y = 0.5000 mm (within |y - 0.5| < 0.005 mm)
    ligament_elements = []
    y_target = 0.5000
    y_tol = 0.0050
    for e_lbl in umatelem_labels:
        xc, yc = elem_centroids[e_lbl]
        if abs(yc - y_target) <= y_tol:
            base_id = e_lbl - 30384 if e_lbl > 30384 else e_lbl
            ligament_elements.append((e_lbl, base_id, xc, yc))
            
    ligament_elements.sort(key=lambda item: item[2])
    print("[INFO] Identified %d ligament elements along y approx 0.5000 mm (x in [%.4f, %.4f])" % 
          (len(ligament_elements), ligament_elements[0][2], ligament_elements[-1][2]))

    matched_results_bundle = []
    all_ligament_profiles_rows = []
    all_contour_rows = []

    for u_target, frame_meta in matched_target_frames:
        s_name = frame_meta['step_name']
        f_idx = frame_meta['frame_idx']
        frame = odb.steps[s_name].frames[f_idx]
        
        print("\nProcessing Matched State u_target = %.6f mm (%s Frame %d)..." % (u_target, s_name, f_idx))
        
        # A. Extract SDV14 Phase Field on companion elements
        elem_d = {}
        d_max_val = 0.0
        
        if 'SDV14' in frame.fieldOutputs:
            s14_field = frame.fieldOutputs['SDV14']
            if umatelem_set is not None:
                s14_sub = s14_field.getSubset(region=umatelem_set)
            else:
                s14_sub = s14_field
                
            for val in s14_sub.values:
                e_lbl = val.elementLabel
                d_v = float(val.data)
                if e_lbl not in elem_d:
                    elem_d[e_lbl] = d_v
                else:
                    elem_d[e_lbl] = max(elem_d[e_lbl], d_v)
                if d_v > d_max_val:
                    d_max_val = d_v

        # B. Strict Element Energy Deduplication
        e_frac_sum = 0.0
        e_elas_sum = 0.0
        
        if 'SDV17' in frame.fieldOutputs and 'SDV18' in frame.fieldOutputs:
            sdv17_field = frame.fieldOutputs['SDV17']
            sdv18_field = frame.fieldOutputs['SDV18']
            
            if umatelem_set is not None:
                sdv17_sub = sdv17_field.getSubset(region=umatelem_set)
                sdv18_sub = sdv18_field.getSubset(region=umatelem_set)
            else:
                sdv17_sub = sdv17_field
                sdv18_sub = sdv18_field
                
            # Group by element label
            elem_17 = {}
            for val in sdv17_sub.values:
                e_lbl = val.elementLabel
                if e_lbl not in elem_17:
                    elem_17[e_lbl] = []
                elem_17[e_lbl].append(float(val.data))
                
            elem_18 = {}
            for val in sdv18_sub.values:
                e_lbl = val.elementLabel
                if e_lbl not in elem_18:
                    elem_18[e_lbl] = []
                elem_18[e_lbl].append(float(val.data))
                
            # Verify within-element equality and take single value
            for e_lbl, vals in elem_17.items():
                first_val = vals[0]
                for v in vals[1:]:
                    if abs(v - first_val) > max(1e-12, 1e-6 * abs(first_val)):
                        raise ValueError("Inconsistent SDV17 Gauss-point values in element %d: %s" % (e_lbl, str(vals)))
                e_frac_sum += first_val
                
            for e_lbl, vals in elem_18.items():
                first_val = vals[0]
                for v in vals[1:]:
                    if abs(v - first_val) > max(1e-12, 1e-6 * abs(first_val)):
                        raise ValueError("Inconsistent SDV18 Gauss-point values in element %d: %s" % (e_lbl, str(vals)))
                e_elas_sum += first_val
                
        e_frac_mJ = e_frac_sum * 1000.0
        e_elas_mJ = e_elas_sum * 1000.0
        e_model_mJ = e_frac_mJ + e_elas_mJ
        w_ext_mJ = frame_meta['w_ext_mJ']
        delta_book_mJ = e_model_mJ - w_ext_mJ
        eps_book_pct = (abs(delta_book_mJ) / max(w_ext_mJ, 1e-12)) * 100.0

        # C. Ligament Profile & Crack-Tip Extent
        ligament_data = []
        x_tip_90 = 0.5000
        x_tip_95 = 0.5000
        
        for e_lbl, base_id, xc, yc in ligament_elements:
            d_val = elem_d.get(e_lbl, 0.0)
            ligament_data.append({
                'element_id': e_lbl,
                'base_element_id': base_id,
                'x_mm': xc,
                'y_mm': yc,
                'd': d_val
            })
            
            all_ligament_profiles_rows.append({
                'u_target_mm': u_target,
                'u_actual_mm': frame_meta['u_mm'],
                'step_name': s_name,
                'frame_idx': f_idx,
                'element_id': e_lbl,
                'base_element_id': base_id,
                'x_mm': xc,
                'y_mm': yc,
                'd': d_val
            })
            
            if xc >= 0.5000:
                if d_val >= 0.90 and xc > x_tip_90:
                    x_tip_90 = xc
                if d_val >= 0.95 and xc > x_tip_95:
                    x_tip_95 = xc

        # D. Contour Mapping Rows (for all companion elements)
        for e_lbl in umatelem_labels:
            xc, yc = elem_centroids[e_lbl]
            base_id = e_lbl - 30384 if e_lbl > 30384 else e_lbl
            d_val = elem_d.get(e_lbl, 0.0)
            all_contour_rows.append({
                'u_target_mm': u_target,
                'u_actual_mm': frame_meta['u_mm'],
                'step_name': s_name,
                'frame_idx': f_idx,
                'element_id': e_lbl,
                'base_element_id': base_id,
                'x_mm': xc,
                'y_mm': yc,
                'd': d_val
            })

        state_record = {
            'u_target_mm': u_target,
            'u_actual_mm': frame_meta['u_mm'],
            'step_name': s_name,
            'frame_idx': f_idx,
            'step_time': frame_meta['step_time'],
            'total_time': frame_meta['total_time'],
            'reaction_force_kN': frame_meta['rf_kN'],
            'd_max': d_max_val,
            'crack_tip_x_d90_mm': x_tip_90,
            'crack_tip_x_d95_mm': x_tip_95,
            'unbroken_ligament_d90_mm': 1.0 - x_tip_90,
            'unbroken_ligament_d95_mm': 1.0 - x_tip_95,
            'w_ext_mJ': w_ext_mJ,
            'w_ext_kNmm': frame_meta['w_ext_kNmm'],
            'e_frac_mJ': e_frac_mJ,
            'e_frac_kNmm': e_frac_sum,
            'e_elas_mJ': e_elas_mJ,
            'e_elas_kNmm': e_elas_sum,
            'e_model_mJ': e_model_mJ,
            'e_model_kNmm': e_frac_sum + e_elas_sum,
            'delta_book_mJ': delta_book_mJ,
            'delta_book_kNmm': delta_book_mJ / 1000.0,
            'eps_book_pct': eps_book_pct,
            'ligament_profile_points': len(ligament_data)
        }
        
        print("  F = %.6f kN | d_max = %.4f | x_tip(0.9) = %.4f mm | W_ext = %.6f mJ | E_frac = %.6f mJ | E_elas = %.6f mJ | Delta_book = %.6f mJ (%.3f%%)" %
              (frame_meta['rf_kN'], d_max_val, x_tip_90, w_ext_mJ, e_frac_mJ, e_elas_mJ, delta_book_mJ, eps_book_pct))
              
        matched_results_bundle.append(state_record)

    odb.close()

    # 4. Write output files (Python 2.7 compatible)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # Master JSON bundle
    bundle_json_path = os.path.join(out_dir, "MODE1_REFERENCE_MATCHED_DISPLACEMENT_BUNDLE.json")
    with open(bundle_json_path, "wb") as fp:
        json.dump({
            'provenance': {
                'job_id': '1409734.mmaster02',
                'mechanical_anchor_job_id': '1398090.mmaster02',
                'model_name': 'PK_MODE1_REF15K_ENERGY',
                'underlying_elements': 15192,
                'nodes': 15521,
                'layers_total_elements': 45576,
                'deck_sha256': 'ec560a4c265730647b43dab125d166ebc57cac285d574d38222a498a967535d9',
                'fortran_sha256': 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6',
                'units': {
                    'length': 'mm',
                    'force': 'kN',
                    'energy': 'mJ',
                    'stress': 'GPa = kN/mm^2'
                },
                'governed_energy_definitions': {
                    'w_ext': 'trapezoidal cumulative work integral_0^u F du',
                    'e_frac': 'implemented phase-field crack-surface/fracture functional integral G_c [d^2/(2 l_0) + (l_0/2)|grad d|^2] dOmega',
                    'e_elas': 'degraded stored elastic strain energy integral (1/2 sigma : epsilon) dOmega',
                    'e_model': 'descriptive sum E_elas + E_frac',
                    'delta_book': 'descriptive bookkeeping difference E_model - W_ext',
                    'eps_book_pct': '|Delta_book| / W_ext * 100%'
                }
            },
            'matched_states': matched_results_bundle
        }, fp, indent=2)
    print("\n[SUCCESS] Wrote master JSON bundle: %s" % bundle_json_path)

    # Matched states summary CSV
    summary_csv_path = os.path.join(out_dir, "mode1_reference_matched_states_summary.csv")
    with open(summary_csv_path, "wb") as fp:
        fieldnames = [
            'u_target_mm', 'u_actual_mm', 'step_name', 'frame_idx', 'step_time', 'total_time',
            'reaction_force_kN', 'd_max', 'crack_tip_x_d90_mm', 'crack_tip_x_d95_mm',
            'unbroken_ligament_d90_mm', 'unbroken_ligament_d95_mm',
            'w_ext_mJ', 'e_frac_mJ', 'e_elas_mJ', 'e_model_mJ', 'delta_book_mJ', 'eps_book_pct'
        ]
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in matched_results_bundle:
            writer.writerow(row)
    print("[SUCCESS] Wrote summary CSV: %s" % summary_csv_path)

    # Ligament profiles CSV
    ligament_csv_path = os.path.join(out_dir, "mode1_reference_ligament_profiles.csv")
    with open(ligament_csv_path, "wb") as fp:
        fieldnames = ['u_target_mm', 'u_actual_mm', 'step_name', 'frame_idx', 'element_id', 'base_element_id', 'x_mm', 'y_mm', 'd']
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_ligament_profiles_rows:
            writer.writerow(row)
    print("[SUCCESS] Wrote ligament profiles CSV (%d rows): %s" % (len(all_ligament_profiles_rows), ligament_csv_path))

    # Contour matched states CSV
    contour_csv_path = os.path.join(out_dir, "mode1_reference_contour_matched_states.csv")
    with open(contour_csv_path, "wb") as fp:
        fieldnames = ['u_target_mm', 'u_actual_mm', 'step_name', 'frame_idx', 'element_id', 'base_element_id', 'x_mm', 'y_mm', 'd']
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_contour_rows:
            writer.writerow(row)
    print("[SUCCESS] Wrote contour matched states CSV (%d rows): %s" % (len(all_contour_rows), contour_csv_path))

    print("\n================================================================================")
    print("EXTRACTION COMPLETE: ALL 10 MATCHED REFERENCE STATES PROCESSED SUCCESSFULLY")
    print("================================================================================")

if __name__ == '__main__':
    odb_p = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/16_energy_qualification_reference_15k/PK_M1_REF15K_ENERGY.odb"
    out_d = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/16_energy_qualification_reference_15k"
    if len(sys.argv) > 1:
        odb_p = sys.argv[1]
    if len(sys.argv) > 2:
        out_d = sys.argv[2]
        
    extract_matched_reference_bundle(odb_p, out_d)
