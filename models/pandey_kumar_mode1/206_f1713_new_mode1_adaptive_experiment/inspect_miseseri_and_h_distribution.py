import os
import sys
import math
import json

base_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\206_f1713_new_mode1_adaptive_experiment"
phys_inp = os.path.join(base_dir, "PK_F1713_JOB2_ADAPTED_PHYS.inp")

# 1. Parse physical mesh to inspect element sizes and h/l0 distribution
nodes = {}
quads = {}
tris = {}

with open(phys_inp, 'r') as f:
    in_nodes = False
    in_elems = False
    elem_type = 'QUAD'
    for line in f:
        l = line.strip()
        if not l or l.startswith('**'):
            continue
        if l.startswith('*'):
            in_nodes = False
            in_elems = False
            if l.upper().startswith('*NODE'):
                in_nodes = True
            elif l.upper().startswith('*ELEMENT'):
                in_elems = True
                if 'CPE3' in l.upper() or 'TRI' in l.upper():
                    elem_type = 'TRI'
                else:
                    elem_type = 'QUAD'
            continue
        if in_nodes:
            parts = [p.strip() for p in l.split(',') if p.strip()]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
        elif in_elems:
            parts = [p.strip() for p in l.split(',') if p.strip()]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    if elem_type == 'QUAD' or len(conn) == 4:
                        quads[eid] = tuple(conn[:4])
                    else:
                        tris[eid] = tuple(conn[:3])
                except ValueError:
                    pass

print("Loaded physical mesh: %d nodes, %d quads, %d tris (Total %d)" % (
    len(nodes), len(quads), len(tris), len(quads) + len(tris)
))

l0 = 0.0075 # mm = 7.5 um

# Compute element size h = sqrt(Area) for each element
elem_h = {}
elem_centroids = {}

for eid, conn in quads.items():
    pts = [nodes[nid] for nid in conn]
    # Shoelace formula for area
    area = 0.5 * abs(
        pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1] +
        pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1] +
        pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1] +
        pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]
    )
    h = math.sqrt(area)
    cx = sum(p[0] for p in pts) / 4.0
    cy = sum(p[1] for p in pts) / 4.0
    elem_h[eid] = h
    elem_centroids[eid] = (cx, cy)

for eid, conn in tris.items():
    pts = [nodes[nid] for nid in conn]
    area = 0.5 * abs(
        pts[0][0]*(pts[1][1] - pts[2][1]) +
        pts[1][0]*(pts[2][1] - pts[0][1]) +
        pts[2][0]*(pts[0][1] - pts[1][1])
    )
    h = math.sqrt(area)
    cx = sum(p[0] for p in pts) / 3.0
    cy = sum(p[1] for p in pts) / 3.0
    elem_h[eid] = h
    elem_centroids[eid] = (cx, cy)

all_h = list(elem_h.values())
print("Global element size h: min = %.4e mm (%.2f um), max = %.4e mm (%.2f um), mean = %.4e mm" % (
    min(all_h), min(all_h)*1000, max(all_h), max(all_h)*1000, sum(all_h)/len(all_h)
))

# Ligament analysis: y in [0.47, 0.53], x in [0.50, 1.0]
ligament_eids = [
    eid for eid, (cx, cy) in elem_centroids.items()
    if 0.47 <= cy <= 0.53 and cx >= 0.50
]
ligament_h = [elem_h[eid] for eid in ligament_eids]
ligament_hl0 = [h / l0 for h in ligament_h]

print("\n--- Ligament Process Zone (x >= 0.50, y in [0.47, 0.53]) ---")
print("Number of elements in ligament zone: %d" % len(ligament_eids))
print("h in ligament zone: min = %.4e mm (%.2f um), max = %.4e mm (%.2f um), mean = %.4e mm (%.2f um)" % (
    min(ligament_h), min(ligament_h)*1000, max(ligament_h), max(ligament_h)*1000,
    sum(ligament_h)/len(ligament_h), sum(ligament_h)/len(ligament_h)*1000
))
print("h / l0 in ligament zone: min = %.3f, max = %.3f, mean = %.3f" % (
    min(ligament_hl0), max(ligament_hl0), sum(ligament_hl0)/len(ligament_hl0)
))

frac_hl0_1 = sum(1 for r in ligament_hl0 if r <= 1.0) / float(len(ligament_hl0))
frac_hl0_05 = sum(1 for r in ligament_hl0 if r <= 0.5) / float(len(ligament_hl0))
frac_hl0_02 = sum(1 for r in ligament_hl0 if r <= 0.2) / float(len(ligament_hl0))

print("Fraction of ligament elements with h <= l0: %.2f%% (%d / %d)" % (
    frac_hl0_1 * 100, sum(1 for r in ligament_hl0 if r <= 1.0), len(ligament_hl0)
))
print("Fraction of ligament elements with h <= l0/2: %.2f%% (%d / %d)" % (
    frac_hl0_05 * 100, sum(1 for r in ligament_hl0 if r <= 0.5), len(ligament_hl0)
))
print("Fraction of ligament elements with h <= l0/5 (<= 1.5 um): %.2f%% (%d / %d)" % (
    frac_hl0_02 * 100, sum(1 for r in ligament_hl0 if r <= 0.2), len(ligament_hl0)
))

# Notch tip process zone: (cx - 0.5)^2 + (cy - 0.5)^2 <= (0.05)^2
notch_eids = [
    eid for eid, (cx, cy) in elem_centroids.items()
    if (cx - 0.5)**2 + (cy - 0.5)**2 <= (0.05)**2
]
notch_h = [elem_h[eid] for eid in notch_eids]
notch_hl0 = [h / l0 for h in notch_h]
print("\n--- Notch Tip Zone (radius <= 0.05 mm from tip) ---")
print("Number of elements at notch tip: %d" % len(notch_eids))
print("h at notch tip: min = %.4e mm (%.2f um), max = %.4e mm (%.2f um), mean = %.4e mm (%.2f um)" % (
    min(notch_h), min(notch_h)*1000, max(notch_h), max(notch_h)*1000,
    sum(notch_h)/len(notch_h), sum(notch_h)/len(notch_h)*1000
))
print("h / l0 at notch tip: min = %.3f, max = %.3f, mean = %.3f" % (
    min(notch_hl0), max(notch_hl0), sum(notch_hl0)/len(notch_hl0)
))

# Output JSON summary
metrics = {
    "n_physical_elements": len(quads) + len(tris),
    "n_nodes": len(nodes),
    "global_h_min_mm": min(all_h),
    "global_h_max_mm": max(all_h),
    "global_h_mean_mm": sum(all_h)/len(all_h),
    "l0_mm": l0,
    "ligament_elements": len(ligament_eids),
    "ligament_h_min_mm": min(ligament_h),
    "ligament_h_max_mm": max(ligament_h),
    "ligament_h_mean_mm": sum(ligament_h)/len(ligament_h),
    "ligament_hl0_min": min(ligament_hl0),
    "ligament_hl0_max": max(ligament_hl0),
    "ligament_hl0_mean": sum(ligament_hl0)/len(ligament_hl0),
    "ligament_fraction_hl0_le_1": frac_hl0_1,
    "ligament_fraction_hl0_le_half": frac_hl0_05,
    "notch_elements": len(notch_eids),
    "notch_h_min_mm": min(notch_h),
    "notch_h_max_mm": max(notch_h),
    "notch_h_mean_mm": sum(notch_h)/len(notch_h),
    "notch_hl0_min": min(notch_hl0),
    "notch_hl0_max": max(notch_hl0),
    "notch_hl0_mean": sum(notch_hl0)/len(notch_hl0)
}

with open(os.path.join(base_dir, "F1713_ADAPTED_MESH_METRICS.json"), "w") as f:
    json.dump(metrics, f, indent=2)
print("\nWrote metrics to F1713_ADAPTED_MESH_METRICS.json")
