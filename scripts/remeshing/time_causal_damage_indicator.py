# -*- coding: utf-8 -*-
"""
scripts/remeshing/time_causal_damage_indicator.py
Task F1749: Reusable, Geometry-Independent, Time-Causal Damage-Aware Refinement
Indicator Module for 2D Phase-Field Fracture in Abaqus.

Core Principles:
1. Strict Temporal Causality: At state t_n, uses ONLY field outputs from t <= t_n.
   Zero future-solution information is leaked into earlier adaptation events.
2. Geometry-Independence: No crack coordinates, notch positions, hole boundaries,
   or geometric refinement corridors are used.
3. Analytical Phase-Field Sizing Law: Inverts the 1D exponential damage profile
   d(x) = exp(-|x|/l0) to guarantee h <= l0/2 in the process zone and h <= l0/3
   at the crack core, with smooth transition to h_coarse in the bulk.
4. Incremental Damage Rate: Tracks Delta d = max(0, d_n - d_{n-1}) to identify
   actively advancing crack fronts.
"""

import os
import json
import csv
import numpy as np

class TimeCausalDamageIndicator:
    """
    Reusable time-causal damage-aware refinement indicator module.
    """
    def __init__(self, char_length_l0, coarse_elem_size_h_bg, core_ratio=3.0, process_ratio=2.0, noise_cutoff=0.05):
        self.l0 = float(char_length_l0)
        self.h_bg = float(coarse_elem_size_h_bg)
        self.h_core = self.l0 / float(core_ratio)        # Default: l0 / 3
        self.h_process = self.l0 / float(process_ratio)   # Default: l0 / 2
        self.d_cut = float(noise_cutoff)                  # Default: 0.05
        
        # Inversion boundaries from d(x) = exp(-|x|/l0)
        # Core zone: |x| <= 0.5 * l0 -> d >= exp(-0.5) ~ 0.6065
        self.d_core = float(np.exp(-0.5))
        # Process zone: |x| <= 1.0 * l0 -> d >= exp(-1.0) ~ 0.3679
        self.d_process = float(np.exp(-1.0))
        # Tail cutoff: |x| <= 3.0 * l0 -> d >= exp(-3.0) ~ 0.0498 ~ d_cut
        self.d_tail = float(np.exp(-3.0))

    def compute_element_target_size(self, d_val):
        """
        Computes physical target element size h(d) via analytical phase-field inversion.
        Guarantees:
        - d >= d_core (~0.606): h = h_core (l0/3)
        - d_process <= d < d_core: h in [h_core, h_process] <= l0/2
        - d_cut <= d < d_process: smooth transition from h_process up to h_bg
        - d < d_cut: h = h_bg (unrefined bulk)
        """
        if d_val < self.d_cut:
            return self.h_bg
        
        # Effective normalized distance from crack centerline in units of l0
        x_norm = -np.log(max(float(d_val), 1e-7))
        
        if x_norm <= 0.5:
            return self.h_core
        elif x_norm <= 1.0:
            # Linear transition in distance space between core (0.5 l0) and process (1.0 l0)
            t = (x_norm - 0.5) / 0.5
            return self.h_core * (1.0 - t) + self.h_process * t
        elif x_norm <= 3.0:
            # Smooth transition between process zone (1.0 l0) and bulk (3.0 l0)
            t = (x_norm - 1.0) / 2.0
            return self.h_process * (1.0 - t) + self.h_bg * t
        else:
            return self.h_bg

    def evaluate_state_indicator(self, d_current, d_previous=None):
        """
        Evaluates the time-causal refinement indicator at the current state.
        Uses ONLY current and historical fields (at or before current time).
        Returns:
            - h_target: array of requested element sizes [mm]
            - indicator_active: boolean mask of refined elements
            - delta_d: incremental damage rate (if previous state provided)
            - target_subdivisions: estimated sub-element count (h_bg / h)^2
        """
        d_curr_arr = np.array(d_current, dtype=float)
        n_elem = len(d_curr_arr)
        
        # Compute incremental damage rate if previous state is provided
        if d_previous is not None:
            d_prev_arr = np.array(d_previous, dtype=float)
            delta_d = np.maximum(0.0, d_curr_arr - d_prev_arr)
        else:
            delta_d = np.zeros(n_elem, dtype=float)
            
        # Element target sizes via analytical inversion
        h_target = np.array([self.compute_element_target_size(d) for d in d_curr_arr])
        
        # Active elements are those where requested size is smaller than background
        indicator_active = d_curr_arr >= self.d_cut
        
        # Estimated 2D subdivision ratio
        target_subdivisions = (self.h_bg / h_target)**2
        
        return {
            "h_target": h_target,
            "indicator_active": indicator_active,
            "delta_d": delta_d,
            "target_subdivisions": target_subdivisions,
            "total_predicted_elements": int(np.sum(target_subdivisions)),
            "active_elements_count": int(np.sum(indicator_active)),
            "active_elements_pct": float(np.sum(indicator_active) / n_elem * 100.0),
            "process_zone_count_h_le_half": int(np.sum(h_target <= self.h_process)),
            "core_zone_count_h_le_third": int(np.sum(h_target <= self.h_core))
        }

def run_causal_case3_audit():
    """
    Evaluates time-causal damage progression across all 5 states of Case 3.
    """
    data_path = "results/validation/f1694_sec43_five_state_damage_record.json"
    with open(data_path, "r", encoding="utf-8") as f:
        d1694 = json.load(f)
        
    audit_path = "results/validation/f1747_contrast_prototype_summary.json"
    with open(audit_path, "r", encoding="utf-8") as f:
        s_f1747 = json.load(f)
        
    prim_eids = [p["eid"] for p in s_f1747["forensic_audit"]["along_path_primary"]]
    sec_eids = [p["eid"] for p in s_f1747["forensic_audit"]["along_path_secondary"]]
    
    # Case 3 parameters: l0 = 0.285 mm, h_bg = 1.367 mm
    indicator = TimeCausalDamageIndicator(char_length_l0=0.285, coarse_elem_size_h_bg=1.367)
    
    states = d1694["states"]
    results = []
    d_prev = None
    
    for idx, st in enumerate(states):
        d_dict = st["damage_by_element"]
        d_curr = [float(d_dict[str(i)]) for i in range(1, 3924)]
        
        eval_res = indicator.evaluate_state_indicator(d_curr, d_prev)
        d_prev = d_curr
        
        # Check along-path corridor coverage at THIS state
        h_arr = eval_res["h_target"]
        prim_h = [h_arr[eid-1] for eid in prim_eids]
        sec_h = [h_arr[eid-1] for eid in sec_eids]
        
        prim_proc_count = sum(1 for h in prim_h if h <= indicator.h_process)
        sec_proc_count = sum(1 for h in sec_h if h <= indicator.h_process)
        
        prim_active_count = sum(1 for eid in prim_eids if d_curr[eid-1] >= indicator.d_cut)
        sec_active_count = sum(1 for eid in sec_eids if d_curr[eid-1] >= indicator.d_cut)
        
        results.append({
            "state_index": idx,
            "state_id": st["state_id"],
            "name": st["name"],
            "uy_mm": st["uy_mm"],
            "rf2_kN": st["rf2_kN"],
            "max_damage": float(np.max(d_curr)),
            "active_elements_count": eval_res["active_elements_count"],
            "active_elements_pct": eval_res["active_elements_pct"],
            "bulk_suppression_pct": float(100.0 - eval_res["active_elements_pct"]),
            "predicted_elements": eval_res["total_predicted_elements"],
            "process_zone_count": eval_res["process_zone_count_h_le_half"],
            "core_zone_count": eval_res["core_zone_count_h_le_third"],
            "primary_corridor_active_count": prim_active_count,
            "primary_corridor_active_pct": float(prim_active_count / len(prim_eids) * 100.0),
            "primary_corridor_process_pct": float(prim_proc_count / len(prim_eids) * 100.0),
            "secondary_corridor_active_count": sec_active_count,
            "secondary_corridor_active_pct": float(sec_active_count / len(sec_eids) * 100.0),
            "secondary_corridor_process_pct": float(sec_proc_count / len(sec_eids) * 100.0),
            "max_incremental_delta_d": float(np.max(eval_res["delta_d"]))
        })
        
    return results

if __name__ == "__main__":
    res = run_causal_case3_audit()
    print("=== Time-Causal Case 3 Progression Audit ===")
    for r in res:
        print("State %d (%-22s, uy=%.2f mm): Predicted=%5d el | Prim Active=%2d/%2d (%5.1f%%) | Sec Active=%2d/%2d (%5.1f%%)" % (
            r["state_index"], r["name"], r["uy_mm"], r["predicted_elements"],
            r["primary_corridor_active_count"], 35, r["primary_corridor_active_pct"],
            r["secondary_corridor_active_count"], 21, r["secondary_corridor_active_pct"]
        ))
