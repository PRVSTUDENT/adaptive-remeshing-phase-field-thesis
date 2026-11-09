import json
import numpy as np

with open('results/validation/f1703_secondary_crack_propagation_timeline.json', 'r') as f:
    timeline = json.load(f)

# Sort frames in chronological order
sorted_frames = sorted(timeline.keys(), key=lambda k: int(k))

print("=" * 80)
print("SECONDARY CRACK PROPAGATION TIMELINE (AUTHENTIC JOB 1421286)")
print(f"{'Frame':>5} {'Time':>7} {'uy (mm)':>8} {'Els (d>=0.5)':>13} {'x_tip (mm)':>11} {'y_tip (mm)':>11} {'Advancement':>12} {'% Ligament':>11}")
print("-" * 80)

for fk in sorted_frames:
    info = timeline[fk]
    fidx = info['frame_index']
    t = info['time']
    uy = info['uy_mm']
    num_els = info['num_sec_cracked_elements_d05']
    tip = info['crack_tip']
    if tip:
        xtip = tip['cx']
        ytip = tip['cy']
    else:
        xtip = 46.50
        ytip = 51.00
    dist = info['dist_from_hole_mm']
    pct = info['pct_ligament']
    print(f"{fidx:5d} {t:7.4f} {uy:8.4f} {num_els:13d} {xtip:11.2f} {ytip:11.2f} {dist:11.2f} mm {pct:10.1f}%")

print("=" * 80)

# Inspect the final crack elements at Frame 100 (complete crossing)
f100 = timeline['100']
sec_els_100 = f100['sec_elements']
print(f"Total secondary crack elements at Frame 100: {len(sec_els_100)}")
xs = [e['cx'] for e in sec_els_100]
ys = [e['cy'] for e in sec_els_100]
damages = [e['damage'] for e in sec_els_100]

print(f"Secondary crack x span: [{min(xs):.2f}, {max(xs):.2f}] mm (Hole boundary: 46.50 mm, Plate edge: 65.00 mm)")
print(f"Secondary crack y span: [{min(ys):.2f}, {max(ys):.2f}] mm (Mean y: {np.mean(ys):.2f} mm)")
print(f"Damage range in secondary corridor: [{min(damages):.4f}, {max(damages):.4f}] (Elements with d >= 0.9: {sum(1 for d in damages if d >= 0.9)})")

# Fit a trajectory line y = m*x + c
p = np.polyfit(xs, ys, 1)
print(f"Linear fit to secondary crack trajectory: y = {p[0]:.4f} * x + {p[1]:.4f}")
print(f"  At hole edge (x = 46.50 mm): y = {p[0]*46.50 + p[1]:.2f} mm")
print(f"  At plate edge (x = 65.00 mm): y = {p[0]*65.00 + p[1]:.2f} mm")
print(f"  Total vertical deviation: {p[0]*(65.00 - 46.50):.2f} mm (slight upward inclination of {np.degrees(np.arctan(p[0])):.2f} deg)")
