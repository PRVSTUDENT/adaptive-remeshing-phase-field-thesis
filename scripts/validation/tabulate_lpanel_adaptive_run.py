import json
import glob
import os

p = 'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run'
files = glob.glob(os.path.join(p, '*_SUMMARY.json'))
sums = [json.load(open(f, 'r', encoding='utf-8')) for f in files]
sums.sort(key=lambda s: s['cycle'])

print("=== CYCLE-BY-CYCLE TELEMETRY ===")
header = f"{'Cycle':>5} | {'Elem':>6} | {'Nodes':>6} | {'uy [mm]':>8} | {'RF2 [kN]':>9} | {'d_max':>6} | {'dRF2 [%]':>9} | {'Tip (x, y)':>18} | {'Chord [mm]':>10} | {'Status':>17}"
print(header)
print("-" * len(header))

for s in sums:
    c = s['cycle']
    elem = s['mesh_elements']
    nodes = s['mesh_nodes']
    uy = s['terminal_uy_mm']
    rf2 = s['terminal_rf2_kn']
    dmax = s['max_damage']
    drf2 = s.get('gate_results', {}).get('force_continuity_delta_pct', 0.0)
    tip = f"({s['tip_mm'][0]:6.2f}, {s['tip_mm'][1]:6.2f})"
    chord = s['tip_history_chord_sum_mm']
    status = s['status']
    print(f"{c:5d} | {elem:6d} | {nodes:6d} | {uy:8.4f} | {rf2:9.5f} | {dmax:6.4f} | {drf2:+8.4f}% | {tip:>18} | {chord:10.2f} | {status:>17}")

print("\n=== IMAGE MANIFEST ===")
manifest_file = os.path.join(p, 'image_manifest.json')
if os.path.exists(manifest_file):
    m = json.load(open(manifest_file, 'r', encoding='utf-8'))
    for e in m:
        print(f"Cycle {e['cycle']:2d}: Commit={e['commit'][:9]} SHA={e['image_sha256'][:16]}... URL={e['url']}")
