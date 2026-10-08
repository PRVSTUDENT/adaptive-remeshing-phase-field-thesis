# -*- coding: utf-8 -*-
"""
extract_mode2_miseseri_deep_audit.py
Comprehensive forensic audit of Mode-II pre-analysis stress and error fields.
Investigates:
1. S (Mises), MISESERI, MISESAVG across Step 1 and Step 2 final frames.
2. Layer 3 companion UMAT scaling factor (E_UMAT = 1e-11 kN/mm^2 vs E_phys = 210 kN/mm^2).
3. Physical stress recovery: sigma_phys = sigma_Layer3 * (210 / 1e-11).
4. Relative error indicator eta_e = MISESERI / MISESAVG scale-invariance.
5. Spatial localization and correlation with Mode-II shear crack corridor.
"""

from __future__ import print_function
import os
import sys
import math
import json
import odbAccess

def run_deep_audit(odb_path, out_dir="."):
    if not os.path.exists(odb_path):
        print("ERROR: ODB path does not exist: %s" % odb_path)
        sys.exit(1)

    print("=" * 80)
    print("MODE-II MISESERI FIELD VALIDITY & 3-LAYER ARCHITECTURE DEEP AUDIT")
    print("ODB: %s" % odb_path)
    print("=" * 80)

    o = odbAccess.openOdb(odb_path, readOnly=True)
    inst_name = o.rootAssembly.instances.keys()[0]
    inst = o.rootAssembly.instances[inst_name]
    nodes = {n.label: n.coordinates for n in inst.nodes}
    elements = {e.label: e.connectivity for e in inst.elements}

    # Physical scaling factor
    E_PHYS = 210.0          # kN/mm^2 (210 GPa)
    E_UMAT = 1.0e-11        # kN/mm^2 (10^-8 MPa)
    STRESS_SCALE_FACTOR = E_PHYS / E_UMAT  # 2.10e13

    # Layer 3 identification
    elem_labels = sorted(elements.keys())
    max_label = max(elem_labels)
    n_phys = max_label // 3 if max_label > 3000 else 2960

    print("Mesh summary: %d total elements, %d nodes, N_phys = %d" % 
          (len(elements), len(nodes), n_phys))
    print("Physical E = %.1f kN/mm^2, Layer 3 E_UMAT = %.1e kN/mm^2" % (E_PHYS, E_UMAT))
    print("Stress scaling factor (E_PHYS / E_UMAT) = %.4e" % STRESS_SCALE_FACTOR)

    results_by_step = {}

    for step_name in ['Step-1', 'Step-2']:
        if step_name not in o.steps.keys():
            print("WARNING: Step '%s' not found in ODB." % step_name)
            continue

        step = o.steps[step_name]
        f_last = step.frames[-1]
        f_id = int(f_last.frameId)
        f_val = float(f_last.frameValue)
        u_top = 0.0100 if step_name == 'Step-1' else 0.0200

        print("\n" + "-" * 70)
        print("ANALYZING STEP: '%s' | Frame %d | FrameValue %.4f | u_top = %.4f mm" % 
              (step_name, f_id, f_val, u_top))
        print("-" * 70)

        # Check fieldOutputs
        fo_keys = list(f_last.fieldOutputs.keys())
        print("Available FieldOutputs: %s" % str(fo_keys))

        fo_miseseri = f_last.fieldOutputs['MISESERI'] if 'MISESERI' in f_last.fieldOutputs.keys() else None
        fo_misesavg = f_last.fieldOutputs['MISESAVG'] if 'MISESAVG' in f_last.fieldOutputs.keys() else None
        fo_s = f_last.fieldOutputs['S'] if 'S' in f_last.fieldOutputs.keys() else None

        records = []
        
        # Build map of S (Mises) per element
        mises_s_map = {}
        if fo_s is not None:
            for v in fo_s.values:
                eid = v.elementLabel
                if v.mises is not None:
                    # Integration point or element average
                    mises_s_map.setdefault(eid, []).append(float(v.mises))
        
        # Build map of MISESAVG per element
        misesavg_map = {}
        if fo_misesavg is not None:
            for v in fo_misesavg.values:
                misesavg_map[v.elementLabel] = float(v.data)

        # Extract MISESERI
        if fo_miseseri is not None:
            for v in fo_miseseri.values:
                eid = v.elementLabel
                miseseri_val = float(v.data)
                
                # Resolve base physical element ID
                if eid > 2 * n_phys:
                    base_eid = eid - 2 * n_phys
                    layer = 3
                elif eid > n_phys:
                    base_eid = eid - n_phys
                    layer = 2
                else:
                    base_eid = eid
                    layer = 1

                # Element coordinates
                conn = elements.get(eid, elements.get(base_eid, []))
                if conn:
                    pts = [nodes[n] for n in conn if n in nodes]
                    xc = sum(p[0] for p in pts) / float(len(pts))
                    yc = sum(p[1] for p in pts) / float(len(pts))
                else:
                    xc, yc = 0.0, 0.0

                misesavg_val = misesavg_map.get(eid, float('nan'))
                s_mises_raw = sum(mises_s_map.get(eid, [0.0])) / float(max(len(mises_s_map.get(eid, [1])), 1))
                
                # Physical reconstructed stresses
                s_mises_phys_kN_mm2 = s_mises_raw * STRESS_SCALE_FACTOR
                s_mises_phys_MPa = s_mises_phys_kN_mm2 * 1000.0  # 1 kN/mm^2 = 1000 MPa

                # Relative error indicator
                eta_e = (miseseri_val / misesavg_val) if (misesavg_val and not math.isnan(misesavg_val) and misesavg_val > 0) else 0.0

                records.append({
                    'eid': eid,
                    'base_eid': base_eid,
                    'layer': layer,
                    'xc': xc,
                    'yc': yc,
                    'miseseri': miseseri_val,
                    'misesavg': misesavg_val,
                    'eta_e': eta_e,
                    's_mises_raw': s_mises_raw,
                    's_mises_phys_MPa': s_mises_phys_MPa
                })

        # Save Step CSV
        csv_filename = os.path.join(out_dir, "mode2_miseseri_deep_audit_%s.csv" % step_name.lower().replace('-', ''))
        with open(csv_filename, "w") as f:
            f.write("base_eid,eid,layer,xc,yc,miseseri,misesavg,eta_e,s_mises_raw,s_mises_phys_MPa\n")
            for r in sorted(records, key=lambda x: x['base_eid']):
                f.write("%d,%d,%d,%.6f,%.6f,%.6e,%.6e,%.6e,%.6e,%.4f\n" % (
                    r['base_eid'], r['eid'], r['layer'], r['xc'], r['yc'],
                    r['miseseri'], r['misesavg'], r['eta_e'], r['s_mises_raw'], r['s_mises_phys_MPa']
                ))
        print("Saved %d element records to: %s" % (len(records), csv_filename))

        # Statistical evaluation
        if records:
            miseseri_vals = [r['miseseri'] for r in records]
            misesavg_vals = [r['misesavg'] for r in records if not math.isnan(r['misesavg'])]
            eta_vals = [r['eta_e'] for r in records]
            s_phys_vals = [r['s_mises_phys_MPa'] for r in records]

            stats = {
                'step': step_name,
                'frame_id': f_id,
                'frame_value': f_val,
                'u_top_mm': u_top,
                'num_elements': len(records),
                'miseseri_min': min(miseseri_vals),
                'miseseri_max': max(miseseri_vals),
                'miseseri_mean': sum(miseseri_vals) / float(len(miseseri_vals)),
                'misesavg_min': min(misesavg_vals) if misesavg_vals else 0.0,
                'misesavg_max': max(misesavg_vals) if misesavg_vals else 0.0,
                'misesavg_mean': sum(misesavg_vals) / float(len(misesavg_vals)) if misesavg_vals else 0.0,
                'eta_min': min(eta_vals),
                'eta_max': max(eta_vals),
                'eta_mean': sum(eta_vals) / float(len(eta_vals)),
                's_phys_MPa_min': min(s_phys_vals),
                's_phys_MPa_max': max(s_phys_vals),
                's_phys_MPa_mean': sum(s_phys_vals) / float(len(s_phys_vals)),
                'dynamic_range_miseseri': max(miseseri_vals) / max(min(miseseri_vals), 1e-25),
                'dynamic_range_s_phys': max(s_phys_vals) / max(min(s_phys_vals), 1e-12)
            }
            results_by_step[step_name] = stats

            print("Statistics for %s:" % step_name)
            print("  MISESERI range:       [%.4e, %.4e] (mean: %.4e)" % 
                  (stats['miseseri_min'], stats['miseseri_max'], stats['miseseri_mean']))
            print("  MISESAVG range:       [%.4e, %.4e] (mean: %.4e)" % 
                  (stats['misesavg_min'], stats['misesavg_max'], stats['misesavg_mean']))
            print("  eta_e (rel error):    [%.6f, %.6f] (mean: %.6f)" % 
                  (stats['eta_min'], stats['eta_max'], stats['eta_mean']))
            print("  Physical Mises (MPa): [%.2f, %.2f] (mean: %.2f MPa)" % 
                  (stats['s_phys_MPa_min'], stats['s_phys_MPa_max'], stats['s_phys_MPa_mean']))
            print("  Dynamic range:        MISESERI = %.1fx, Stress = %.1fx" % 
                  (stats['dynamic_range_miseseri'], stats['dynamic_range_s_phys']))

    o.close()

    # Step 2 vs Step 1 scaling check
    if 'Step-1' in results_by_step and 'Step-2' in results_by_step:
        s1 = results_by_step['Step-1']
        s2 = results_by_step['Step-2']
        
        ratio_miseseri_max = s2['miseseri_max'] / s1['miseseri_max']
        ratio_misesavg_mean = s2['misesavg_mean'] / s1['misesavg_mean']
        ratio_eta_max = s2['eta_max'] / s1['eta_max']
        ratio_s_phys_max = s2['s_phys_MPa_max'] / s1['s_phys_MPa_max']

        print("\n" + "=" * 70)
        print("STEP 2 VS STEP 1 RATIO COMPARISON (Theoretical = 2.000000x):")
        print("  Ratio MISESERI max:     %.6f" % ratio_miseseri_max)
        print("  Ratio MISESAVG mean:    %.6f" % ratio_misesavg_mean)
        print("  Ratio eta_e max:        %.6f (Bit-for-bit invariance = 1.000000)" % ratio_eta_max)
        print("  Ratio Phys Stress max:  %.6f" % ratio_s_phys_max)
        print("=" * 70)

        results_by_step['ratios_step2_to_step1'] = {
            'ratio_miseseri_max': ratio_miseseri_max,
            'ratio_misesavg_mean': ratio_misesavg_mean,
            'ratio_eta_max': ratio_eta_max,
            'ratio_s_phys_max': ratio_s_phys_max,
            'mathematical_scale_invariance_verified': bool(abs(ratio_eta_max - 1.0) < 1e-6)
        }

    # Save summary JSON
    summary_path = os.path.join(out_dir, "mode2_miseseri_deep_audit_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results_by_step, f, indent=4)
    print("Saved deep audit summary to: %s" % summary_path)

if __name__ == "__main__":
    odb_target = sys.argv[1] if len(sys.argv) > 1 else "Job-1_UEL_paper_horizon.odb"
    out_target = sys.argv[2] if len(sys.argv) > 2 else "."
    run_deep_audit(odb_target, out_target)
