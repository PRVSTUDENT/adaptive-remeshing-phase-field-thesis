#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/remeshing/tabulate_f1813_progression.py
Tabulates the four-benchmark progression across Tasks F1808, F1809, F1811, and F1812.
"""

import json
import os
import sys

def main():
    receipts = {
        'F1808': 'models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json',
        'F1809': 'models/pandey_kumar_mode1/259_f1809_multistate_recovery/PK_F1809_MULTISTATE_SEQUENTIAL_RECEIPT.json',
        'F1811': 'models/pandey_kumar_mode1/260_f1811_error_target_calibration/PK_F1811_ERROR_TARGET_CALIBRATION_RECEIPT.json',
        'F1812': 'models/pandey_kumar_mode1/261_f1812_crack_path_refinement/PK_F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_RECEIPT.json',
    }

    all_data = {}
    for task_name, rpath in receipts.items():
        if not os.path.exists(rpath):
            print("Missing: %s" % rpath)
            continue
        with open(rpath, 'r') as f:
            all_data[task_name] = json.load(f)

    cases = ['case_1', 'case_2', 'case_3', 'case_5']
    case_names = {
        'case_1': 'Case 1 (Mode-I Edge Crack)',
        'case_2': 'Case 2 (Off-Axis Hole)',
        'case_3': 'Case 3 (Hole with Pins)',
        'case_5': 'Case 5 (Seven Holes)'
    }

    print("\n================ FOUR-BENCHMARK CAMPAIGN PROGRESSION ================\n")

    summary_table = {}

    for c in cases:
        print("--- %s ---" % case_names[c])
        print("%-8s | %-6s | %-8s | %-8s | %-8s | %-8s | %-8s | %s" % (
            "Task", "eta_R", "Elements", "Quad %", "Min detJ", "Max AR", "Coarsen", "Critical Metric & Gate"
        ))
        print("-" * 95)
        summary_table[c] = []
        for t in ['F1808', 'F1809', 'F1811', 'F1812']:
            data = all_data[t]
            c_dict = data.get('selected_cases', data.get('cases', {}))
            c_data = c_dict.get(c, {})
            eta = c_data.get('error_target', 'N/A')
            audit = c_data.get('audit', {})
            n_elem = audit.get('total_elements', audit.get('total_physical_elements', 0))
            quad_pct = audit.get('quad_percent', audit.get('quad_fraction_pct', 0.0))
            min_detj = audit.get('min_det_j', audit.get('min_signed_jacobian', 0.0))
            max_ar = audit.get('max_aspect_ratio', 0.0)
            coarsening = audit.get('refinement_ratio_far_to_core', 0.0)
            crit = c_data.get('critical_metrics', {})
            gates = c_data.get('gates', {})

            crit_desc = ""
            gate_status = "N/A"
            if c == 'case_1':
                if t in ['F1808', 'F1809']:
                    crit_desc = "Full Ligament: 79.8% <= l0/2 (Incomplete)"
                    gate_status = "INCOMPLETE"
                elif t == 'F1811':
                    crit_desc = "Tip: 100.0% <= l0/2 in 0.05mm tip box (Distal 0.0%, Incomplete)"
                    gate_status = "INCOMPLETE"
                else:
                    crit_desc = "Full Ligament: 97.2% <= l0/2"
                    gate_status = "PASS"
            elif c == 'case_2':
                cov = crit.get('combined_outer_ligament_pct_le_l0_half', 0.0)
                crit_desc = "Outer lig: %.1f%% <= l0/2" % cov
                gate_status = gates.get('SCIENTIFIC_GATE_OUTER_DISTAL', 'FAIL')
            elif c == 'case_3':
                cov = crit.get('secondary_pct_le_l0', 0.0)
                crit_desc = "Sec corr: %.1f%% <= l0" % cov
                gate_status = gates.get('SCIENTIFIC_GATE_SECONDARY_CORRIDOR', 'INCOMPLETE')
            elif c == 'case_5':
                cov = crit.get('upper_pct_le_l0', 0.0)
                crit_desc = "Inter-hole: %.1f%% <= l0" % cov
                gate_status = gates.get('SCIENTIFIC_GATE_INTER_HOLE', 'PASS')

            entry = {
                'task': t,
                'error_target': eta,
                'elements': n_elem,
                'quad_pct': quad_pct,
                'min_detj': min_detj,
                'max_ar': max_ar,
                'coarsening': coarsening,
                'crit_desc': crit_desc,
                'gate_status': gate_status
            }
            summary_table[c].append(entry)

            print("%-8s | %-6s | %-8d | %-7.2f%% | %-8.2e | %-8.2f | %-7.2fx | %s [%s]" % (
                t, str(eta), n_elem, quad_pct, min_detj, max_ar, coarsening, crit_desc, gate_status
            ))
        print("\n")

    # Export progression summary json
    out_dir = "models/pandey_kumar_mode1/262_f1813_unified_synthesis"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with open(os.path.join(out_dir, "campaign_progression_summary.json"), "w") as f:
        json.dump(summary_table, f, indent=2)
    print("Saved progression summary to %s" % os.path.join(out_dir, "campaign_progression_summary.json"))

if __name__ == '__main__':
    main()
