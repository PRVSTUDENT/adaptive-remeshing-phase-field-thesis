# -*- coding: utf-8 -*-
"""
analyze_transient_donors.py
===========================
Analyzes the downloaded historical damage records from Task 192/194/199
to inspect intermediate crack propagation states between the notch and hole.
"""
import json
import os

def analyze():
    p1 = "results/validation/f1694_sec43_five_state_damage_record.json"
    p2 = "results/validation/f1699_uel_accepted_states.json"
    p3 = "results/validation/secondary_crack_propagation_timeline.json"

    print("=== Analyzing f1694_sec43_five_state_damage_record.json ===")
    if os.path.exists(p1):
        with open(p1, "r", encoding="utf-8") as f:
            d1 = json.load(f)
        states = d1.get("states", [])
        print("Found %d states in f1694:" % len(states))
        for i, s in enumerate(states):
            name = s.get("name", "State %d" % i)
            sid = s.get("state_id", "")
            uy = s.get("uy_mm", 0.0)
            rf2 = s.get("rf2_kN", 0.0)
            max_p = s.get("max_damage_primary", 0.0)
            max_s = s.get("max_damage_secondary", 0.0)
            n_broken = s.get("n_elements_d_gt_090", 0)
            print("  [%d] %s (%s): uy=%.3f mm, RF2=%.3f kN, max_d_prim=%.4f, max_d_sec=%.4f, n(d>0.9)=%d" % (
                i, name, sid, uy, rf2, max_p, max_s, n_broken))

    print("\n=== Analyzing f1699_uel_accepted_states.json ===")
    if os.path.exists(p2):
        with open(p2, "r", encoding="utf-8") as f:
            d2 = json.load(f)
        print("Type:", type(d2))
        if isinstance(d2, dict):
            print("Keys:", list(d2.keys()))
            for k in d2.keys():
                v = d2[k]
                if isinstance(v, list):
                    print("  %s: list of len %d" % (k, len(v)))
                elif isinstance(v, dict):
                    print("  %s: dict of keys %s" % (k, list(v.keys())[:5]))
                else:
                    print("  %s: %s" % (k, str(v)[:50]))
        elif isinstance(d2, list):
            print("List of len %d" % len(d2))
            for i, item in enumerate(d2[:5]):
                print("  [%d]: %s" % (i, str(item)[:80]))

    print("\n=== Analyzing secondary_crack_propagation_timeline.json ===")
    if os.path.exists(p3):
        with open(p3, "r", encoding="utf-8") as f:
            d3 = json.load(f)
        print("Type:", type(d3))
        if isinstance(d3, list):
            print("List of %d frames" % len(d3))
            print("Sample first 3 and last 3:")
            for item in d3[:3]:
                print("  ", item)
            for item in d3[-3:]:
                print("  ", item)
        elif isinstance(d3, dict):
            print("Keys:", list(d3.keys()))

if __name__ == "__main__":
    analyze()
