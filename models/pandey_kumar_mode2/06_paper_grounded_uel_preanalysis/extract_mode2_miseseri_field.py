# -*- coding: utf-8 -*-
"""
Extract and evaluate raw pre-adaptive MISESERI and SDV fields from Job-1_UEL.odb.
Governing Reference: Pandey & Kumar (2025) CMES, Section 4.2, Fig. 6(b).
"""

from __future__ import print_function
import os
import sys
import math
import json
import odbAccess

DIGITIZED_FIG6B = [
    (0.495, 0.514), (0.540, 0.460), (0.600, 0.380),
    (0.680, 0.280), (0.760, 0.180), (0.840, 0.080), (0.930, 0.000)
]

def extract_mode2_miseseri(odb_path="Job-1_UEL.odb", out_dir="."):
    if not os.path.exists(odb_path):
        print("ERROR: ODB not found: %s" % odb_path)
        sys.exit(1)

    o = odbAccess.openOdb(odb_path, readOnly=True)
    step_name = o.steps.keys()[-1] # use latest available step
    step = o.steps[step_name]
    f_last = step.frames[-1]

    print("=" * 70)
    print("MODE-II RAW MISESERI EXTRACTION & LOCALIZATION AUDIT")
    print("ODB: %s" % odb_path)
    print("Step: '%s', Frame: %d, Time: %.5f" % (step_name, f_last.frameId, f_last.frameValue))
    print("=" * 70)

    # Get instance
    inst_name = o.rootAssembly.instances.keys()[0]
    inst = o.rootAssembly.instances[inst_name]
    nodes = {n.label: n.coordinates for n in inst.nodes}
    elements = {e.label: e.connectivity for e in inst.elements}

    # Extract MISESERI
    if 'MISESERI' not in f_last.fieldOutputs:
        print("ERROR: MISESERI not in fieldOutputs. Available:", f_last.fieldOutputs.keys())
        o.close()
        sys.exit(1)

    fo_miseseri = f_last.fieldOutputs['MISESERI']
    
    # Layer 3 elements are (2*N_phys+1)..3*N_phys
    # Determine N_phys
    elem_labels = sorted(elements.keys())
    max_label = max(elem_labels)
    n_phys = max_label // 3 if max_label > 3000 else 2960

    records = []
    for v in fo_miseseri.values:
        eid = v.elementLabel
        miseseri_val = float(v.data)
        base_eid = eid - 2 * n_phys if eid > 2 * n_phys else (eid - n_phys if eid > n_phys else eid)
        
        conn = elements.get(eid, elements.get(base_eid, []))
        if conn:
            pts = [nodes[n] for n in conn if n in nodes]
            if pts:
                xc = sum(p[0] for p in pts) / float(len(pts))
                yc = sum(p[1] for p in pts) / float(len(pts))
            else:
                xc, yc = 0.0, 0.0
        else:
            xc, yc = 0.0, 0.0

        records.append({
            'eid': eid,
            'base_eid': base_eid,
            'xc': xc,
            'yc': yc,
            'miseseri': miseseri_val
        })

    o.close()

    # Save to CSV
    csv_path = os.path.join(out_dir, "miseseri_raw_field.csv")
    with open(csv_path, "w") as f:
        f.write("base_eid,layer3_eid,xc,yc,miseseri\n")
        for r in sorted(records, key=lambda x: x['base_eid']):
            f.write("%d,%d,%.6f,%.6f,%.6e\n" % (r['base_eid'], r['eid'], r['xc'], r['yc'], r['miseseri']))
    print("Saved %d MISESERI records to %s" % (len(records), csv_path))

    # Top corridor analysis
    records_sorted = sorted(records, key=lambda x: x['miseseri'], reverse=True)
    max_miseseri = records_sorted[0]['miseseri']
    mean_miseseri = sum(r['miseseri'] for r in records) / float(len(records))

    print("\nMax MISESERI = %.4e, Mean MISESERI = %.4e, Ratio = %.1fx" % 
          (max_miseseri, mean_miseseri, max_miseseri / max(mean_miseseri, 1e-12)))

    # Identify corridor centerline: elements with MISESERI > 5% of max in x >= 0.45, y in [0, 0.55]
    corridor_elems = [r for r in records if r['miseseri'] > 0.05 * max_miseseri and r['xc'] >= 0.45 and r['yc'] <= 0.55]
    
    y_bins = [0.05 * i for i in range(11)]
    centerline = []
    for y_val in y_bins:
        band = [r for r in corridor_elems if abs(r['yc'] - y_val) <= 0.035]
        if band:
            mean_x = sum(r['xc'] for r in band) / float(len(band))
            centerline.append((mean_x, y_val))

    if len(centerline) >= 2:
        start_pt = max(centerline, key=lambda p: p[1])
        end_pt = min(centerline, key=lambda p: p[1])
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        chord_angle = math.degrees(math.atan2(dy, dx))
        end_x = end_pt[0]
    else:
        chord_angle = 0.0
        end_x = 0.5

    # Check spurious branches (high error in upper quadrant y > 0.55 away from boundaries)
    spurious = [r for r in records if r['miseseri'] > 0.10 * max_miseseri and r['yc'] > 0.55 and 0.10 < r['xc'] < 0.90]
    has_spurious = len(spurious) > 20

    # Verdict
    if -58.0 <= chord_angle <= -42.0 and 0.80 <= end_x <= 0.98 and not has_spurious:
        verdict = "MODE2_MISESERI_LOCALIZATION_CONSISTENT_WITH_PUBLISHED_PATH"
    elif not has_spurious and end_x > 0.70:
        verdict = "MODE2_MISESERI_LOCALIZATION_PARTIALLY_CONSISTENT"
    else:
        verdict = "MODE2_MISESERI_LOCALIZATION_INCONSISTENT"

    summary = {
        'odb_path': odb_path,
        'step_name': step_name,
        'frame_id': f_last.frameId,
        'frame_value': f_last.frameValue,
        'total_elements': len(records),
        'max_miseseri': max_miseseri,
        'mean_miseseri': mean_miseseri,
        'corridor_chord_angle_deg': chord_angle,
        'corridor_exit_x': end_x,
        'has_spurious_branches': has_spurious,
        'spurious_count': len(spurious),
        'verdict': verdict,
        'centerline_points': centerline,
        'fig6b_reference_chord_deg': -49.74,
        'fig6b_reference_exit_x': 0.930
    }

    json_path = os.path.join(out_dir, "MODE2_MISESERI_LOCALIZATION_SUMMARY.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved localization summary to %s" % json_path)
    print("\nCorridor Chord Angle: %.2f deg (Published Fig 6b: ~-49.74 deg)" % chord_angle)
    print("Corridor Exit X at y=0: %.3f mm (Published Fig 6b: ~0.930 mm)" % end_x)
    print("Spurious Branches in Upper Domain: %s (Count: %d)" % (has_spurious, len(spurious)))
    print("Governing Verdict: %s" % verdict)
    return summary

if __name__ == "__main__":
    odb_p = sys.argv[1] if len(sys.argv) >= 2 else "Job-1_UEL.odb"
    out_d = sys.argv[2] if len(sys.argv) >= 3 else "."
    extract_mode2_miseseri(odb_p, out_d)
