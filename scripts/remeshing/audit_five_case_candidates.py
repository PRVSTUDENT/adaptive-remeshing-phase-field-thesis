# -*- coding: utf-8 -*-
import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def audit_candidates():
    inv_path = os.path.join(REPO_ROOT, "results", "validation", "f1736_mesh_inventory.json")
    with open(inv_path, "r") as f:
        data = json.load(f)

    keywords = [
        "219_f1728",
        "224_f1734",
        "223_f1732",
        "222_f1731",
        "207_f1727",
        "188_pk_sec43",
        "190_pk_sec43",
        "192_pk_sec43",
        "seven_hole",
        "five_hole",
        "case_1",
        "case_2",
        "case_3",
        "case_4",
        "case_5",
        "f1725",
        "f1726",
        "f1724",
        "f1719"
    ]
    
    matches = [m for m in data if any(k in m["rel_path"].lower() for k in keywords)]
    print("\n--- MATCHING CANDIDATE PHYSICAL MESHES ---")
    for m in sorted(matches, key=lambda x: (x["total_elements"], x["rel_path"])):
        print("{:6d} el ({:5.1f}% Q, {:4d} T, {:6d} N) | {}".format(
            m["total_elements"], m["quad_pct"], m["tris"], m["nodes"], m["rel_path"]
        ))
    
    return matches

if __name__ == "__main__":
    audit_candidates()
