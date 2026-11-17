# -*- coding: utf-8 -*-
"""
scripts/remeshing/diagnose_f1834_early_states.py
================================================
Task F1834: Quantitative Diagnosis of Early-State Eta Blowup across Cases 1, 2, 3.
Reads solved recovery ODBs, measures instantaneous MISESAVG_k vs peak MISESAVG,
and computes elementwise state dominance: which state determines max(eta_e)?
"""
from __future__ import print_function
import os
import sys
import json
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import odbAccess

def analyze_case(case_name, solved_odbs, step_name="RECOVERY_STEP"):
    print("\n" + "=" * 80)
    print("DIAGNOSIS FOR %s (%d STATES)" % (case_name.upper(), len(solved_odbs)))
    print("=" * 80)

    states_data = []
    elem_labels = None

    for idx, path in enumerate(solved_odbs):
        o = odbAccess.openOdb(path, readOnly=True)
        step = o.steps[step_name]
        f = step.frames[-1]
        eri_fo = f.fieldOutputs["MISESERI"]
        avg_fo = f.fieldOutputs["MISESAVG"]

        eri_dict = {v.elementLabel: float(v.data) for v in eri_fo.values}
        avg_dict = {v.elementLabel: float(v.data) for v in avg_fo.values}
        o.close()

        if elem_labels is None:
            elem_labels = sorted(eri_dict.keys())

        # Instantaneous domain average MISESAVG
        mean_avg = sum(avg_dict.values()) / float(len(avg_dict)) if avg_dict else 0.0

        # Elementwise relative error
        eta_dict = {}
        for el in elem_labels:
            el_avg = avg_dict.get(el, 0.0)
            el_eri = eri_dict.get(el, 0.0)
            eta_dict[el] = (el_eri / el_avg) if el_avg > 0.0 else 0.0

        states_data.append({
            "index": idx,
            "filename": os.path.basename(path),
            "mean_avg": mean_avg,
            "eri_dict": eri_dict,
            "avg_dict": avg_dict,
            "eta_dict": eta_dict
        })

    # Find peak state mean_avg
    peak_avg = max(s["mean_avg"] for s in states_data)

    print("State Stress Hierarchy (MISESAVG relative to peak):")
    for s in states_data:
        ratio = (s["mean_avg"] / peak_avg) * 100.0 if peak_avg > 0 else 0.0
        max_eta = max(s["eta_dict"].values()) if s["eta_dict"] else 0.0
        mean_eta = sum(s["eta_dict"].values()) / float(len(s["eta_dict"])) if s["eta_dict"] else 0.0
        print("  State %d: %-35s | MISESAVG: %10.4f MPa (%5.1f%% of peak) | Max eta: %8.2f%% | Mean eta: %6.2f%%" % (
            s["index"], s["filename"], s["mean_avg"], ratio, max_eta * 100.0, mean_eta * 100.0
        ))

    # Determine which state determines max(eta) for each element
    state_dominance_counts = {s["index"]: 0 for s in states_data}
    element_winner = {}
    max_eta_all = {}

    for el in elem_labels:
        best_state = -1
        best_eta = -1.0
        for s in states_data:
            eta = s["eta_dict"][el]
            if eta > best_eta:
                best_eta = eta
                best_state = s["index"]
        element_winner[el] = best_state
        max_eta_all[el] = best_eta
        state_dominance_counts[best_state] += 1

    total_elems = len(elem_labels)
    print("\nState Envelope Dominance Breakdown (Total Elements: %d):" % total_elems)
    for s in states_data:
        cnt = state_dominance_counts[s["index"]]
        pct = (cnt / float(total_elems)) * 100.0
        ratio = (s["mean_avg"] / peak_avg) * 100.0
        print("  State %d (%5.1f%% load): %6d elements determine max(eta) (%5.1f%% of all elements)" % (
            s["index"], ratio, cnt, pct
        ))

    return {
        "case": case_name,
        "peak_avg": peak_avg,
        "states": [
            {
                "index": s["index"],
                "filename": s["filename"],
                "mean_avg": s["mean_avg"],
                "load_ratio_pct": round((s["mean_avg"] / peak_avg) * 100.0, 2),
                "dominant_elements": state_dominance_counts[s["index"]],
                "dominant_fraction_pct": round((state_dominance_counts[s["index"]] / float(total_elems)) * 100.0, 2),
                "max_eta_pct": round(max(s["eta_dict"].values()) * 100.0, 2),
                "mean_eta_pct": round((sum(s["eta_dict"].values()) / float(len(s["eta_dict"]))) * 100.0, 2)
            }
            for s in states_data
        ]
    }


def main():
    results = {}

    # Case 1
    c1_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1")
    c1_odbs = [
        os.path.join(c1_dir, "PK_C1_STATE1_INITIATION.odb"),
        os.path.join(c1_dir, "PK_C1_STATE2_EARLY_PROPAGATION.odb"),
        os.path.join(c1_dir, "PK_C1_STATE3_MID_PROPAGATION.odb"),
        os.path.join(c1_dir, "PK_C1_STATE4_OUTER_PROPAGATION.odb"),
        os.path.join(c1_dir, "PK_C1_STATE5_TERMINAL_SEVERANCE.odb")
    ]
    results["case_1"] = analyze_case("Case 1 (Mode-I Edge Crack)", c1_odbs)

    # Case 2
    c2_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
    c2_odbs = [
        os.path.join(c2_dir, "PK_C2_STATE1_PREANALYSIS.odb"),
        os.path.join(c2_dir, "PK_C2_STATE2_HOLE_ARREST.odb"),
        os.path.join(c2_dir, "PK_C2_STATE3_DISTAL_NUCLEATION.odb"),
        os.path.join(c2_dir, "PK_C2_STATE4_OUTER_PROPAGATION.odb")
    ]
    results["case_2"] = analyze_case("Case 2 (Plate with Off-Axis Hole)", c2_odbs)

    # Case 3
    c3_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")
    c3_odbs = [
        os.path.join(c3_dir, "SEC43_C3_STATE1_INITIATION.odb"),
        os.path.join(c3_dir, "SEC43_C3_STATE2_HOLE_ARREST.odb"),
        os.path.join(c3_dir, "SEC43_C3_STATE3_PROPAGATION.odb")
    ]
    results["case_3"] = analyze_case("Case 3 (Notched Plate with Pins and Hole)", c3_odbs)

    out_json = os.path.join(REPO_ROOT, "results", "validation", "f1834_early_state_diagnosis.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("\nDiagnosis results saved to %s" % out_json)


if __name__ == "__main__":
    main()
