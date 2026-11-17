# -*- coding: utf-8 -*-
"""
scripts/remeshing/compute_f1836_per_element_decomposition.py
===========================================================
Computes element-by-element multi-state envelope decomposition for Cases 2 and 3
directly from the primary solved recovery donor ODBs.

For every element:
- Identifies driving state k*(e) that maximizes eta_{e,k} = MISESERI_{e,k} / MISESAVG_{e,k}
- Records driving MISESERI, local MISESAVG, domain mean MISESAVG, ratio, and element volume (EVOL)
- Evaluates whether threshold exceedance is driven by small local denominator
  (MISESERI / domain_mean_MISESAVG < eta_R while MISESERI / local_MISESAVG >= eta_R)
  vs max_k accumulation of genuinely high MISESERI (MISESERI / domain_mean_MISESAVG >= eta_R)
- Exports complete dataset to results/validation/f1836_per_element_envelope_decomposition.json
"""
from __future__ import print_function
import os
import sys
import json
import math

try:
    from odbAccess import openOdb
except ImportError:
    print("FATAL: Must be executed with Abaqus python (SMAPython) containing odbAccess.")
    sys.exit(1)

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"

def compute_case_decomposition(case_id, state_paths, error_target_pct):
    print("\n" + "="*80)
    print("COMPUTING PER-ELEMENT DECOMPOSITION FOR %s (Target: %.2f%%)" % (case_id.upper(), error_target_pct))
    print("="*80)
    
    # 1. Read each state's primary fields
    per_state_data = []
    for sidx, spath in enumerate(state_paths):
        if not os.path.exists(spath):
            raise IOError("Missing state ODB: %s" % spath)
        odb = openOdb(spath, readOnly=True)
        step_name = list(odb.steps.keys())[-1]
        step = odb.steps[step_name]
        frame = step.frames[-1]
        
        eri_raw = {v.elementLabel: float(v.data) for v in frame.fieldOutputs['MISESERI'].values}
        avg_raw = {v.elementLabel: float(v.data) for v in frame.fieldOutputs['MISESAVG'].values}
        ev_raw = {v.elementLabel: float(v.data) for v in frame.fieldOutputs['EVOL'].values} if 'EVOL' in frame.fieldOutputs else {}
        odb.close()
        
        domain_avg = sum(avg_raw.values()) / float(len(avg_raw)) if avg_raw else 0.0
        fname = os.path.basename(spath)
        print("  State %d: %-35s | Domain Mean Stress: %10.4f MPa | Elements: %d" % (
            sidx + 1, fname, domain_avg, len(avg_raw)
        ))
        per_state_data.append({
            "state_index": sidx,
            "state_name": fname,
            "domain_avg": domain_avg,
            "eri": eri_raw,
            "avg": avg_raw,
            "ev": ev_raw
        })

    elem_labels = sorted(per_state_data[0]["eri"].keys())
    elements = []
    
    num_exceed = 0
    num_small_denom = 0
    num_high_eri = 0
    state_dominance = {}
    
    for el in elem_labels:
        evol = per_state_data[0]["ev"].get(el, 1.0)
        max_ratio = -1.0
        best_state_idx = 0
        best_eri = 0.0
        best_avg = 0.0
        best_domain_avg = 0.0
        
        for s in per_state_data:
            e_val = s["eri"][el]
            a_val = s["avg"][el]
            r = (e_val / a_val) if a_val > 0.0 else 0.0
            if r > max_ratio:
                max_ratio = r
                best_state_idx = s["state_index"]
                best_eri = e_val
                best_avg = a_val
                best_domain_avg = s["domain_avg"]
                
        ratio_pct = max_ratio * 100.0
        domain_norm_pct = (best_eri / best_domain_avg * 100.0) if best_domain_avg > 0 else 0.0
        
        exceeds = (ratio_pct >= error_target_pct)
        state_name = per_state_data[best_state_idx]["state_name"]
        state_dominance[state_name] = state_dominance.get(state_name, 0) + 1
        
        if exceeds:
            num_exceed += 1
            if domain_norm_pct < error_target_pct:
                mechanism = "SMALL_LOCAL_DENOMINATOR"
                num_small_denom += 1
            else:
                mechanism = "HIGH_MISESERI"
                num_high_eri += 1
        else:
            mechanism = "BELOW_TARGET"
            
        elements.append({
            "element_label": el,
            "driving_state_index": best_state_idx,
            "driving_state_name": state_name,
            "miseseri": best_eri,
            "local_misesavg": best_avg,
            "domain_mean_misesavg": best_domain_avg,
            "ratio_pct": ratio_pct,
            "domain_normalized_ratio_pct": domain_norm_pct,
            "element_volume": evol,
            "exceeds_threshold": exceeds,
            "mechanism": mechanism
        })
        
    domain_frac = (num_exceed / float(len(elem_labels))) * 100.0
    denom_frac = (num_small_denom / float(num_exceed) * 100.0) if num_exceed > 0 else 0.0
    high_eri_frac = (num_high_eri / float(num_exceed) * 100.0) if num_exceed > 0 else 0.0
    
    print("\nSummary for %s:" % case_id.upper())
    print("  Total Coarse Elements:                 %d" % len(elem_labels))
    print("  Elements Exceeding Target (>= %.2f%%):  %d (%.2f%% of domain)" % (error_target_pct, num_exceed, domain_frac))
    print("  Driven by High MISESERI:               %d (%.2f%% of fine elements, %.2f%% of domain)" % (
        num_high_eri, high_eri_frac, (num_high_eri / float(len(elem_labels))) * 100.0
    ))
    print("  Driven by Small Local Denominator:     %d (%.2f%% of fine elements, %.2f%% of domain)" % (
        num_small_denom, denom_frac, (num_small_denom / float(len(elem_labels))) * 100.0
    ))
    print("  State Dominance Breakdown:")
    for sname, scnt in sorted(state_dominance.items()):
        print("    %-35s: %5d elements (%.2f%%)" % (sname, scnt, (scnt / float(len(elem_labels))) * 100.0))
        
    return {
        "case_id": case_id,
        "error_target_pct": error_target_pct,
        "num_coarse_elements": len(elem_labels),
        "num_elements_exceeding_threshold": num_exceed,
        "domain_fraction_exceeding_threshold_pct": domain_frac,
        "num_exceeding_via_high_miseseri": num_high_eri,
        "fraction_due_to_high_miseseri_of_fine_pct": high_eri_frac,
        "num_exceeding_via_small_local_denominator": num_small_denom,
        "fraction_due_to_small_local_denominator_of_fine_pct": denom_frac,
        "state_dominance_counts": state_dominance,
        "elements": elements
    }

def main():
    c2_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
    c2_states = [
        os.path.join(c2_dir, "PK_C2_STATE1_PREANALYSIS.odb"),
        os.path.join(c2_dir, "PK_C2_STATE2_HOLE_ARREST.odb"),
        os.path.join(c2_dir, "PK_C2_STATE3_DISTAL_NUCLEATION.odb"),
        os.path.join(c2_dir, "PK_C2_STATE4_OUTER_PROPAGATION.odb")
    ]
    c2_summary = compute_case_decomposition("case_2", c2_states, error_target_pct=4.0)

    c3_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")
    c3_states = [
        os.path.join(c3_dir, "SEC43_C3_STATE1_INITIATION.odb"),
        os.path.join(c3_dir, "SEC43_C3_STATE2_HOLE_ARREST.odb"),
        os.path.join(c3_dir, "SEC43_C3_STATE3_PROPAGATION.odb")
    ]
    c3_summary = compute_case_decomposition("case_3", c3_states, error_target_pct=3.0)

    output_path = os.path.join(REPO_ROOT, "results", "validation", "f1836_per_element_envelope_decomposition.json")
    out_data = {
        "task_id": "F1836-F1835-REPORT-CORRECTION",
        "description": "Per-element multi-state envelope decomposition for Cases 2 and 3 recomputed directly from primary ODB fields",
        "case_2": c2_summary,
        "case_3": c3_summary
    }

    with open(output_path, "w") as f:
        json.dump(out_data, f, indent=2)

    sz = os.path.getsize(output_path)
    print("\n" + "="*80)
    print("SAVED PER-ELEMENT DECOMPOSITION TO:")
    print("  Path: %s" % output_path)
    print("  Size: %d bytes (%.2f MB)" % (sz, sz / (1024.0 * 1024.0)))
    print("="*80)

if __name__ == "__main__":
    main()
