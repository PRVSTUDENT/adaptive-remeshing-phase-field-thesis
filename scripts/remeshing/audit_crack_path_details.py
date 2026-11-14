import csv
import json
import math

inp = 'models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_ADAPT_PHYS.inp'
sdv_csv = 'results/validation/f1735_case2_final_frame_sdv.csv'

nodes = {}
elements = {}
with open(inp) as f:
    r_n, r_e = False, False
    for line in f:
        l = line.strip().upper()
        if not l or l.startswith('**'): continue
        if l.startswith('*NODE'): r_n, r_e = True, False; continue
        elif l.startswith('*ELEMENT') and not l.startswith('*ELEMENT OUTPUT'): r_n, r_e = False, True; continue
        elif l.startswith('*'): r_n, r_e = False, False; continue
        p = [x.strip() for x in line.strip().split(',')]
        if r_n:
            try: nodes[int(p[0])] = (float(p[1]), float(p[2]))
            except: pass
        elif r_e:
            try: elements[int(p[0])] = [int(x) for x in p[1:]]
            except: pass

centroids = {eid: (sum(nodes[n][0] for n in c)/len(c), sum(nodes[n][1] for n in c)/len(c)) for eid, c in elements.items()}
sdv = {int(r[0]): float(r[1]) for r in csv.reader(open(sdv_csv)) if r[0]!='physical_element_id'}

left_lig = [eid for eid, d in sdv.items() if d >= 0.95 and centroids[eid][0] <= 0.65]
right_lig = [eid for eid, d in sdv.items() if d >= 0.95 and centroids[eid][0] >= 0.75]

print('Left ligament (x <= 0.65) d >= 0.95 count:', len(left_lig))
print('Right ligament (x >= 0.75) d >= 0.95 count:', len(right_lig))

if left_lig:
    xs = [centroids[eid][0] for eid in left_lig]
    ys = [centroids[eid][1] for eid in left_lig]
    print('Left lig: x in [%.4f, %.4f], y in [%.4f, %.4f]' % (min(xs), max(xs), min(ys), max(ys)))
    
if right_lig:
    xs = [centroids[eid][0] for eid in right_lig]
    ys = [centroids[eid][1] for eid in right_lig]
    print('Right lig: x in [%.4f, %.4f], y in [%.4f, %.4f]' % (min(xs), max(xs), min(ys), max(ys)))

# Check elements near hole boundary
hole_center = (0.65, 0.65)
hole_radius = 0.10
dists_to_boundary = [math.sqrt((centroids[eid][0] - hole_center[0])**2 + (centroids[eid][1] - hole_center[1])**2) - hole_radius for eid in left_lig]
print('Left ligament min distance to hole boundary:', min(dists_to_boundary))
print('Left ligament max distance to hole boundary:', max(dists_to_boundary))

notch_tip = (0.50, 0.50)
dists_to_notch = [math.sqrt((centroids[eid][0] - notch_tip[0])**2 + (centroids[eid][1] - notch_tip[1])**2) for eid in left_lig]
print('Left ligament min distance to notch tip:', min(dists_to_notch))
print('Left ligament max distance to notch tip:', max(dists_to_notch))
