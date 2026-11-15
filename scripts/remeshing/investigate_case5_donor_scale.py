# -*- coding: utf-8 -*-
"""
scripts/remeshing/investigate_case5_donor_scale.py
=================================================
Investigates the field magnitudes, instances, and frame progression in
PK_F1726_SEVEN_HOLE_COARSE.odb to explain the order 1e-14 MISESERI and stress values.
"""

from __future__ import print_function
import os
import sys
import json
from odbAccess import openOdb

def main():
    odb_path = "/scratch9/pr21vyci/runs/mode1_pk_f1774_regression_batch/PK_F1726_SEVEN_HOLE_COARSE.odb"
    if len(sys.argv) > 1:
        odb_path = sys.argv[1]

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    print("ODB Title: %s" % odb.description)
    print("Steps in ODB: %s" % list(odb.steps.keys()))

    for step_name, step in odb.steps.items():
        print("\n=== Step: %s (Total Frames: %d, TimePeriod: %g) ===" % (
            step_name, len(step.frames), float(step.timePeriod) if hasattr(step, 'timePeriod') else 0.0
        ))
        # Sample frames: 0, 1, middle, last
        n_f = len(step.frames)
        sample_indices = sorted(list(set([0, 1, n_f // 4, n_f // 2, 3 * n_f // 4, n_f - 1])))
        for f_idx in sample_indices:
            frame = step.frames[f_idx]
            f_val = float(frame.frameValue)
            f_desc = str(frame.description)
            print("  Frame %d (value=%g, desc='%s'):" % (f_idx, f_val, f_desc))
            for fld_name in ['MISESERI', 'MISESAVG', 'S', 'SDV1', 'SDV2', 'U', 'RF']:
                if fld_name in frame.fieldOutputs:
                    fld = frame.fieldOutputs[fld_name]
                    # collect sample values
                    vals = []
                    for v in fld.values:
                        if v.data is not None:
                            try:
                                if hasattr(v.data, '__iter__'):
                                    vals.append(float(v.data[0]))
                                else:
                                    vals.append(float(v.data))
                            except Exception:
                                pass
                    if vals:
                        print("    %s: min=%g, max=%g, mean=%g (count=%d)" % (
                            fld_name, min(vals), max(vals), sum(vals)/float(len(vals)), len(vals)
                        ))
                    else:
                        print("    %s: present with 0 values" % fld_name)
                else:
                    pass

            # Compute relative error ratio MISESERI / (MISESERI + MISESAVG) if both present
            if 'MISESERI' in frame.fieldOutputs and 'MISESAVG' in frame.fieldOutputs:
                eri_fld = frame.fieldOutputs['MISESERI']
                avg_fld = frame.fieldOutputs['MISESAVG']
                eri_map = {v.elementLabel: float(v.data) for v in eri_fld.values if v.data is not None and v.elementLabel is not None}
                avg_map = {v.elementLabel: float(v.data) for v in avg_fld.values if v.data is not None and v.elementLabel is not None}
                ratios = []
                # Map element centroid y
                inst = odb.rootAssembly.instances['PART-1-1']
                node_map = {n.label: n.coordinates for n in inst.nodes}
                el_map = {e.label: [n for n in e.connectivity] for e in inst.elements}
                y_above = []
                for el_lbl, eri_val in eri_map.items():
                    avg_val = avg_map.get(el_lbl, 0.0)
                    denom = eri_val + avg_val
                    if denom > 0.0:
                        eta = eri_val / denom * 100.0
                        ratios.append(eta)
                        if eta > 5.68 and el_lbl in el_map:
                            conn = el_map[el_lbl]
                            yc = sum(node_map[nl][1] for nl in conn)/float(len(conn))
                            y_above.append(yc)
                if ratios:
                    print("    RELATIVE_ERROR_ETA (%%): min=%.2f%%, max=%.2f%%, mean=%.2f%% (count=%d)" % (
                        min(ratios), max(ratios), sum(ratios)/float(len(ratios)), len(ratios)
                    ))
                    n_above = len(y_above)
                    print("    Elements exceeding target 5.68%%: %d / %d (%.2f%%)" % (
                        n_above, len(ratios), 100.0 * n_above / float(len(ratios))
                    ))
                    if y_above:
                        print("    Spatial distribution of eta > 5.68%%: mean_y=%.4f mm, min_y=%.4f mm, max_y=%.4f mm" % (
                            sum(y_above)/float(len(y_above)), min(y_above), max(y_above)
                        ))
                        for y_lo in [0.0, 0.2, 0.4, 0.6, 0.8]:
                            cnt = sum(1 for y in y_above if y_lo <= y < y_lo + 0.2)
                            print("      y in [%.1f, %.1f): %d elements (%.1f%% of refined elements)" % (
                                y_lo, y_lo + 0.2, cnt, 100.0 * cnt / float(len(y_above))
                            ))

    # Also inspect instances and element sets
    root_assembly = odb.rootAssembly
    print("\n=== Assembly Instances ===")
    for iname, inst in root_assembly.instances.items():
        print("  Instance %s: %d elements, %d nodes" % (iname, len(inst.elements), len(inst.nodes)))
        print("    Element Sets: %s" % list(inst.elementSets.keys()))
        print("    Element types: %s" % list(set([e.type for e in inst.elements])))

    odb.close()
    print("\nInvestigation complete.")

if __name__ == "__main__":
    main()
