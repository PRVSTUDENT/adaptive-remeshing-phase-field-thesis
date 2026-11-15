# -*- coding: utf-8 -*-
import os, sys, math, json, importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
audit_script_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "audit_case1_ligament_resolution.py")
spec = importlib.util.spec_from_file_location("audit_case1", audit_script_path)
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)
parse_inp_mesh = audit_mod.parse_inp_mesh

mesh_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "239_f1772_case1_remesh", "PK_F1728_CASE_1_ADAPT_PHYS.inp")
nodes, elements, elem_types = parse_inp_mesh(mesh_path)

aspect_ratios = []
for eid, conn in elements.items():
    pts = [nodes[n] for n in conn if n in nodes]
    if len(pts) == 4:
        # Quad edges
        e1 = math.hypot(pts[1][0]-pts[0][0], pts[1][1]-pts[0][1])
        e2 = math.hypot(pts[2][0]-pts[1][0], pts[2][1]-pts[1][1])
        e3 = math.hypot(pts[3][0]-pts[2][0], pts[3][1]-pts[2][1])
        e4 = math.hypot(pts[0][0]-pts[3][0], pts[0][1]-pts[3][1])
        edges = [e1, e2, e3, e4]
        min_e = min(edges)
        max_e = max(edges)
        ar = max_e / min_e if min_e > 0 else 1.0
        aspect_ratios.append(ar)
    elif len(pts) == 3:
        e1 = math.hypot(pts[1][0]-pts[0][0], pts[1][1]-pts[0][1])
        e2 = math.hypot(pts[2][0]-pts[1][0], pts[2][1]-pts[1][1])
        e3 = math.hypot(pts[0][0]-pts[2][0], pts[0][1]-pts[2][1])
        edges = [e1, e2, e3]
        min_e = min(edges)
        max_e = max(edges)
        ar = max_e / min_e if min_e > 0 else 1.0
        aspect_ratios.append(ar)

mean_ar = sum(aspect_ratios) / len(aspect_ratios)
max_ar = max(aspect_ratios)
median_ar = sorted(aspect_ratios)[len(aspect_ratios)//2]

print("=== Case 1 Aspect Ratio Audit ===")
print("Total Elements:  %d" % len(aspect_ratios))
print("Mean Aspect Ratio:   %.4f (Target <= 1.50)" % mean_ar)
print("Median Aspect Ratio: %.4f" % median_ar)
print("Max Aspect Ratio:    %.4f (Target <= 4.00)" % max_ar)
print("G4 Mean AR <= 1.50:  %s" % ("PASS" if mean_ar <= 1.50 else "FAIL"))
