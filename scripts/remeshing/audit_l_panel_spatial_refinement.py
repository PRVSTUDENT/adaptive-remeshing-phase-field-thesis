# -*- coding: utf-8 -*-
import os
import sys
import math

sys.path.insert(0, os.getcwd())
from scripts.remeshing.generalized_2d_adaptive_framework_f1846 import MeshQualityAuditEngine

nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(
    'models/pandey_kumar_mode1/276_f1846_generalized_framework/l_panel/PK_F1846_UNFAMILIAR_L_PANEL_ADAPT_PHYS.inp'
)

dists = []
for eid, conn in quads.items():
    pts = [nodes[n] for n in conn]
    cx = sum(p[0] for p in pts) / 4.0
    cy = sum(p[1] for p in pts) / 4.0
    x, y = [p[0] for p in pts], [p[1] for p in pts]
    area = 0.5 * abs((x[0]*y[1]-x[1]*y[0]) + (x[1]*y[2]-x[2]*y[1]) + (x[2]*y[3]-x[3]*y[2]) + (x[3]*y[0]-x[0]*y[3]))
    h = math.sqrt(area)
    d = math.hypot(cx - 50.0, cy - 50.0)
    dists.append((d, h, cx, cy))

dists.sort()
print("Total elements analyzed:", len(dists))
print("Nearest 5 elements to re-entrant corner (50.0, 50.0):")
for d, h, cx, cy in dists[:5]:
    print("  dist=%.2f mm, h=%.3f mm, pos=(%.2f, %.2f)" % (d, h, cx, cy))

print("\nFarthest 5 elements from re-entrant corner (50.0, 50.0):")
for d, h, cx, cy in dists[-5:]:
    print("  dist=%.2f mm, h=%.3f mm, pos=(%.2f, %.2f)" % (d, h, cx, cy))

near_h = [h for d, h, _, _ in dists if d <= 10.0]
far_h = [h for d, h, _, _ in dists if d >= 40.0]
print("\nMean h within 10 mm of corner: %.3f mm (%d elements)" % (sum(near_h)/len(near_h), len(near_h)))
print("Mean h beyond 40 mm of corner: %.3f mm (%d elements)" % (sum(far_h)/len(far_h), len(far_h)))
print("Refinement ratio (far / corner): %.2fx" % ((sum(far_h)/len(far_h)) / (sum(near_h)/len(near_h))))
