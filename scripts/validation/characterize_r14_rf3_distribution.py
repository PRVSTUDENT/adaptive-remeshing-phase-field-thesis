import sys
import numpy as np
from odbAccess import openOdb

odb_path = '/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r14/M1_C3_ACTIVE_SET_R14_IT1.odb'
odb = openOdb(odb_path)
step = odb.steps['Inc1-Coupled']
frame = step.frames[-1]
rf = frame.fieldOutputs['RF']
root_assembly = odb.rootAssembly
instance = root_assembly.instances.values()[0]

node_coords = {n.label: n.coordinates for n in instance.nodes}

# Read d0 from stage_a_all_d0_boundary_cards.inc
d0_dict = {}
with open('/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r14/stage_a_all_d0_boundary_cards.inc') as f:
    for line in f:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            d0_dict[int(parts[0])] = float(parts[3])

rf3_vals = []
for val in rf.values:
    nid = val.nodeLabel
    if nid in node_coords:
        rf3_vals.append((nid, val.data[2]))

rf3_vals.sort(key=lambda x: x[1])
rf3_arr = np.array([x[1] for x in rf3_vals])

print("=================================================================")
print("R14 ITERATION-1 RF3 / LAGRANGE MULTIPLIER CHARACTERIZATION REPORT")
print("=================================================================")
print("Total evaluated nodes: %d" % len(rf3_arr))
print("Min RF3 (most driving): %14.6e kN/mm" % np.min(rf3_arr))
print("Max RF3 (most holding): %14.6e kN/mm" % np.max(rf3_arr))
print("Negative RF3 count:     %d (%.2f%%)" % (np.sum(rf3_arr < 0), 100.0 * np.sum(rf3_arr < 0) / len(rf3_arr)))
print("Positive RF3 count:     %d (%.2f%%)" % (np.sum(rf3_arr > 0), 100.0 * np.sum(rf3_arr > 0) / len(rf3_arr)))

print("\n--- Percentiles of RF3 ---")
for p in [0, 1, 2, 5, 10, 25, 50, 75, 90, 95, 98, 99, 100]:
    print("P%3d: %14.6e kN/mm" % (p, np.percentile(rf3_arr, p)))

print("\n--- Candidate Release Counts at Candidate Thresholds ---")
thresholds = [1e-9, 5e-9, 1e-8, 2e-8, 5e-8, 1e-7, 1.5e-7, 2e-7]
tip_x, tip_y = 0.04125, 0.05000

for tau in thresholds:
    cand = [item for item in rf3_vals if item[1] < -tau]
    count = len(cand)
    if count > 0:
        dists = [np.sqrt((node_coords[n][0] - tip_x)**2 + (node_coords[n][1] - tip_y)**2) for n, _ in cand]
        d0_cand = [d0_dict.get(n, 0.0) for n, _ in cand]
        d0_over_05 = sum(1 for d in d0_cand if d >= 0.5)
        d0_over_02 = sum(1 for d in d0_cand if d >= 0.2)
        print("tau = %9.1e kN/mm | Count: %4d | Max dist from tip: %7.4f mm | d0>=0.5: %2d | d0>=0.2: %4d" % (
            tau, count, max(dists), d0_over_05, d0_over_02
        ))
    else:
        print("tau = %9.1e kN/mm | Count: %4d" % (tau, 0))

print("\n--- Nodes with RF3 < -1.0e-7 kN/mm (Top Driving Nodes) ---")
for n, r in rf3_vals:
    if r < -1.0e-7:
        x, y, _ = node_coords[n]
        d = d0_dict.get(n, 0.0)
        dist = np.sqrt((x - tip_x)**2 + (y - tip_y)**2)
        print("Node %5d: X=%7.4f, Y=%7.4f | dist=%7.4f mm | d0=%7.4f | RF3=%14.6e kN/mm" % (
            n, x, y, dist, d, r
        ))

odb.close()
