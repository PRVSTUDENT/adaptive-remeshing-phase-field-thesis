# -*- coding: utf-8 -*-
"""
scripts/audit/audit_f1719_miseseri_evolution.py
==============================================
Task F1719 Phase 6:
Audit Spatial MISESERI Correlation and Crack Corridor Evolution across
Authentic Coarse States (States 0, 1, 2, 3, 4).

Quantifies:
1. Four-ligament regional error distribution:
   - Ligament 1: Left free boundary to Hole 1 (x in [0.00, 0.25], y in [0.35, 0.65])
   - Ligament 2: Hole 1 to Hole 2 (x in [0.25, 0.55], y in [0.35, 0.65])
   - Ligament 3: Hole 2 to Hole 3 to Hole 4 (Narrowest ligament h3-h4, clearance 33.1 um)
   - Ligament 4: Hole 4 to Right Boundary / Hole 5 (x in [0.75, 1.00], y in [0.35, 0.65])
2. Statistical correlation between authentic coarse damage d_e and MISESERI / eta_e.
3. Proportionality between physical and dummy recovery scales.
4. Saves structured audit to results/validation/f1719_miseseri_evolution_audit.json.
"""

from __future__ import print_function
import os
import sys
import json
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
RECOVERY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_recovered_miseseri_multistate.json")
OUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_miseseri_evolution_audit.json")


def define_ligaments(centroids):
    """
    Classifies elements into four distinct ligament corridors and bulk.
    """
    ligaments = {
        "L1_left_to_h1": [],
        "L2_h1_to_h2": [],
        "L3_h3_to_h4_narrowest": [],
        "L4_h4_to_right": [],
        "bulk": []
    }

    for eid, (cx, cy) in centroids.items():
        # Narrowest ligament h3-h4: x in [0.62, 0.70], y in [0.47, 0.56]
        if 0.62 <= cx <= 0.70 and 0.47 <= cy <= 0.56:
            ligaments["L3_h3_to_h4_narrowest"].append(eid)
        elif 0.0 <= cx <= 0.25 and 0.35 <= cy <= 0.65:
            ligaments["L1_left_to_h1"].append(eid)
        elif 0.25 < cx <= 0.55 and 0.35 <= cy <= 0.65:
            ligaments["L2_h1_to_h2"].append(eid)
        elif 0.75 <= cx <= 1.00 and 0.35 <= cy <= 0.65:
            ligaments["L4_h4_to_right"].append(eid)
        else:
            ligaments["bulk"].append(eid)

    return ligaments


def pearson_correlation(x, y):
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / float(n)
    mean_y = sum(y) / float(n)
    var_x = sum((xi - mean_x)**2 for xi in x)
    var_y = sum((yi - mean_y)**2 for yi in y)
    if var_x <= 1e-20 or var_y <= 1e-20:
        return 0.0
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    return cov / math.sqrt(var_x * var_y)


def main():
    print("=" * 80)
    print("TASK F1719 PHASE 6: SPATIAL MISESERI CORRELATION & CRACK CORRIDOR AUDIT")
    print("=" * 80)

    if not os.path.exists(RECOVERY_JSON):
        raise IOError(f"Recovery JSON not found: {RECOVERY_JSON}")

    with open(RECOVERY_JSON, "r") as f:
        rec_data = json.load(f)

    states = rec_data["states"]
    state_names = ["STATE0", "STATE1", "STATE2", "STATE3", "STATE4"]

    # Extract centroids from STATE0 element_data
    elem_data_s0 = states["STATE0"]["element_data"]
    centroids = {int(k): (v["cx"], v["cy"]) for k, v in elem_data_s0.items()}
    ligaments = define_ligaments(centroids)

    print(f"Elements partition: L1={len(ligaments['L1_left_to_h1'])}, L2={len(ligaments['L2_h1_to_h2'])}, "
          f"L3={len(ligaments['L3_h3_to_h4_narrowest'])}, L4={len(ligaments['L4_h4_to_right'])}, bulk={len(ligaments['bulk'])}")

    audit_results = {
        "task_id": "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE",
        "ligament_element_counts": {k: len(v) for k, v in ligaments.items()},
        "state_evolution": {},
        "proportionality_check": {}
    }

    # 1. State-by-state ligament analysis
    for sname in state_names:
        if sname not in states:
            continue
        sdata = states[sname]
        phys_fields = sdata["scales"]["physical"]["element_fields"]
        elem_data = sdata["element_data"]

        lig_stats = {}
        all_eids = sorted([int(k) for k in phys_fields.keys()])

        damages = [elem_data[str(eid)]["damage"] for eid in all_eids]
        miseseri = [phys_fields[str(eid)]["miseseri"] for eid in all_eids]
        etas = [phys_fields[str(eid)]["eta_percent"] for eid in all_eids]

        # Correlation between damage and MISESERI
        r_d_miseseri = pearson_correlation(damages, miseseri)
        r_d_eta = pearson_correlation(damages, etas)

        for lname, eids in ligaments.items():
            l_errors = [phys_fields[str(eid)]["miseseri"] for eid in eids if str(eid) in phys_fields]
            l_etas = [phys_fields[str(eid)]["eta_percent"] for eid in eids if str(eid) in phys_fields]
            l_damages = [elem_data[str(eid)]["damage"] for eid in eids if str(eid) in elem_data]

            lig_stats[lname] = {
                "num_elements": len(eids),
                "damage_max": max(l_damages) if l_damages else 0.0,
                "damage_mean": sum(l_damages) / float(len(l_damages)) if l_damages else 0.0,
                "miseseri_max": max(l_errors) if l_errors else 0.0,
                "miseseri_mean": sum(l_errors) / float(len(l_errors)) if l_errors else 0.0,
                "eta_max_percent": max(l_etas) if l_etas else 0.0,
                "eta_mean_percent": sum(l_etas) / float(len(l_etas)) if l_etas else 0.0
            }

        # Check top error element
        summary = sdata["scales"]["physical"]["summary"]
        top_elem = summary["top5_error_elements"][0]

        audit_results["state_evolution"][sname] = {
            "desc": sdata["desc"],
            "uy_mm": sdata["uy_mm"],
            "d_max_global": sdata["d_max"],
            "d_mean_global": sdata["d_mean"],
            "miseseri_max_global": summary["miseseri_max"],
            "miseseri_mean_global": summary["miseseri_mean"],
            "eta_max_global": summary["eta_max_percent"],
            "eta_mean_global": summary["eta_mean_percent"],
            "top_element": top_elem,
            "pearson_r_damage_vs_miseseri": r_d_miseseri,
            "pearson_r_damage_vs_eta": r_d_eta,
            "ligaments": lig_stats
        }

        print(f"\n[{sname}] uy = {sdata['uy_mm']:.6f} mm, d_max = {sdata['d_max']:.4f}")
        print(f"  Top Element: ID={top_elem['eid']} at ({top_elem['cx']:.4f}, {top_elem['cy']:.4f}), err={top_elem['miseseri']:.2f} MPa, d={top_elem['damage']:.4f}")
        print(f"  Narrowest Ligament (h3-h4): err_max={lig_stats['L3_h3_to_h4_narrowest']['miseseri_max']:.2f} MPa, d_max={lig_stats['L3_h3_to_h4_narrowest']['damage_max']:.4f}")
        print(f"  Damage vs MISESERI Pearson r = {r_d_miseseri:.4f}, Damage vs eta Pearson r = {r_d_eta:.4f}")

    # 2. Check scale proportionality for State 2 and State 3 (Physical vs Dummy)
    for sname in ["STATE2", "STATE3"]:
        if "dummy" in states[sname]["scales"]:
            phys = states[sname]["scales"]["physical"]["element_fields"]
            dummy = states[sname]["scales"]["dummy"]["element_fields"]

            ratios = []
            delta_etas = []
            for eid_str in phys:
                p_err = phys[eid_str]["miseseri"]
                d_err = dummy[eid_str]["miseseri"]
                p_eta = phys[eid_str]["eta_percent"]
                d_eta = dummy[eid_str]["eta_percent"]

                if d_err > 1e-25:
                    ratios.append(p_err / d_err)
                delta_etas.append(abs(p_eta - d_eta))

            mean_ratio = sum(ratios) / float(len(ratios)) if ratios else 0.0
            max_delta_eta = max(delta_etas) if delta_etas else 0.0

            # Theoretical ratio: 210,000 / 1e-8 = 2.1e+13
            theoretical_ratio = 210000.0 / 1.0e-8

            audit_results["proportionality_check"][sname] = {
                "theoretical_ratio": theoretical_ratio,
                "measured_mean_ratio": mean_ratio,
                "max_delta_eta_percent": max_delta_eta,
                "scale_invariance_verified": bool(max_delta_eta < 1e-4)
            }
            print(f"\nScale Proportionality Check for {sname}:")
            print(f"  Theoretical Ratio: {theoretical_ratio:.6e}")
            print(f"  Measured Mean Ratio: {mean_ratio:.6e} (discrepancy: {abs(mean_ratio - theoretical_ratio) / theoretical_ratio * 100:.6f}%)")
            print(f"  Max |Delta eta|: {max_delta_eta:.6e}% (Invariance PASS: {max_delta_eta < 1e-4})")

    # Save to JSON
    with open(OUT_JSON, "w") as f:
        json.dump(audit_results, f, indent=2)
    print(f"\nSUCCESS: Spatial MISESERI audit saved to {OUT_JSON}")


if __name__ == "__main__":
    main()
