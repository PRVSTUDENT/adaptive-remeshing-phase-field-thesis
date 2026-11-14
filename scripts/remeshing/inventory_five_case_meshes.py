# -*- coding: utf-8 -*-
"""
scripts/remeshing/inventory_five_case_meshes.py
Scans the repository for candidate physical adapted mesh INP files across all five benchmark cases:
- Case 1: Mode-I Straight Notch Edge-Cracked Plate
- Case 2: Original Off-Axis Hole Plate
- Case 3: Rectangular Notched Plate with Hole and Pin Holes
- Case 4: Five-Hole Plate
- Case 5: Seven-Hole Plate
"""

import os
import re
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def count_inp_mesh(inp_path):
    quads = 0
    tris = 0
    nodes = 0
    reading_nodes = False
    reading_elements = False
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip().upper()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*NODE"):
                reading_nodes = True
                reading_elements = False
                continue
            elif l.startswith("*ELEMENT") and not l.startswith("*ELEMENT OUTPUT"):
                reading_nodes = False
                reading_elements = True
                continue
            elif l.startswith("*"):
                reading_nodes = False
                reading_elements = False
                continue
            
            p = [x.strip() for x in line.split(",") if x.strip()]
            if reading_nodes:
                nodes += 1
            elif reading_elements:
                if len(p) == 5:
                    quads += 1
                elif len(p) == 4:
                    tris += 1
    return nodes, quads, tris, quads + tris

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print(f"Scanning models directory for candidate physical meshes...")
    models_dir = os.path.join(REPO_ROOT, "models")
    candidates = []
    
    for root, dirs, files in os.walk(models_dir):
        for f in files:
            if f.endswith(".inp") and ("PHYS" in f or "ADAPT" in f or "sec43" in f or "seven" in f or "five" in f or "hole" in f):
                p = os.path.join(root, f)
                rel = os.path.relpath(p, REPO_ROOT)
                # Quick filter to avoid huge layered decks (over 5MB)
                sz = os.path.getsize(p)
                if sz < 10 * 1024 * 1024:
                    try:
                        n, q, t, tot = count_inp_mesh(p)
                        if tot > 500:
                            candidates.append({
                                "rel_path": rel,
                                "nodes": n,
                                "quads": q,
                                "tris": t,
                                "total_elements": tot,
                                "quad_pct": (q / tot * 100) if tot > 0 else 0,
                                "size_bytes": sz,
                                "sha256": sha256_file(p)
                            })
                    except Exception as e:
                        pass

    print(f"Found {len(candidates)} candidate meshes:")
    print("-" * 110)
    print(f"{'Path':<65} | {'Elems':<7} | {'Quads':<6} | {'Tris':<5} | {'Quad%':<6} | {'Nodes':<6}")
    print("-" * 110)
    for c in sorted(candidates, key=lambda x: x["rel_path"]):
        print(f"{c['rel_path']:<65} | {c['total_elements']:<7} | {c['quads']:<6} | {c['tris']:<5} | {c['quad_pct']:<6.1f} | {c['nodes']:<6}")

    import json
    with open(os.path.join(REPO_ROOT, "results", "validation", "f1736_mesh_inventory.json"), "w") as jf:
        json.dump(candidates, jf, indent=2)

if __name__ == "__main__":
    main()
