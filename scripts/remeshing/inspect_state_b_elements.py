# -*- coding: utf-8 -*-
"""
inspect_state_b_elements.py
===========================
Inspects element damage and centroid positions in State a, State b, State c, State d.
"""
import json

def inspect():
    with open("results/validation/f1694_sec43_five_state_damage_record.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    
    with open("results/validation/f1699_uel_accepted_states.json", "r", encoding="utf-8") as f:
        d2 = json.load(f)
    
    centroids = d2.get("phys_centroids", {})
    print("Total centroids available:", len(centroids))

    for s in d.get("states", []):
        name = s.get("name")
        uy = s.get("uy_mm")
        dmg = s.get("damage_by_element", {})
        
        # Elements with d > 0.5 and d > 0.8
        d_gt_05 = []
        d_gt_08 = []
        for eid_str, val in dmg.items():
            if val >= 0.5:
                c = centroids.get(eid_str, (0.0, 0.0))
                d_gt_05.append((int(eid_str), val, c[0], c[1]))
            if val >= 0.8:
                c = centroids.get(eid_str, (0.0, 0.0))
                d_gt_08.append((int(eid_str), val, c[0], c[1]))

        print("\n" + "="*80)
        print("%s (uy = %.3f mm): %d elements d >= 0.5, %d elements d >= 0.8" % (name, uy, len(d_gt_05), len(d_gt_08)))
        print("="*80)
        
        # Sort by x coordinate
        d_gt_08.sort(key=lambda x: x[2])
        print("Elements with d >= 0.8 (sorted by x):")
        for eid, val, cx, cy in d_gt_08:
            print("  Elem %4d: d=%.4f, cx=%6.2f, cy=%6.2f" % (eid, val, cx, cy))

if __name__ == "__main__":
    inspect()
