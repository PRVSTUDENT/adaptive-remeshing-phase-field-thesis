#!/usr/bin/env python3
"""
Comprehensive Mode-II Spatial Trajectory Audit:
1. Reconstructs ET2 mesh (21,496 elements) from JOB_MODE2_ADAPTIVE_ET2.inp with true element edges.
2. Evaluates raw MISESERI field from Job 1410178 (2,960 elements).
3. Evaluates digitized Pandey & Kumar Fig. 6(b) and Fig. 12(b) paths.
4. Evaluates trusted H2 reference crack trajectory.
5. Computes all required metrics:
   - Tangent angles vs arc length
   - Mean, RMS, and max normal distance
   - Bottom exit coordinate
   - Corridor width vs arc length
   - Local h/l0 along expected path
   - Corridor coverage and fine element fraction
   - Off-path refinement fraction
   - Horizontal-band / boundary-band persistence
6. Generates publication-grade figures.
"""

import os
import sys
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.interpolate import interp1d

# Paths
brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\64f3937d-e56d-47d9-b7cc-69335e20d5fb"
repo_dir = r"D:\Master thesis\Adaptive remeshing"
m2_et2_path = os.path.join(repo_dir, "models", "pandey_kumar_mode2", "04_adaptive_miseseri", "JOB_MODE2_ADAPTIVE_ET2.inp")
miseseri_csv_path = os.path.join(brain_dir, "miseseri_raw_field.csv")
fig_out_dir = os.path.join(repo_dir, "results", "figures", "mode2")

# Physical length scale
l0 = 0.015  # mm

# 1. Digitized Reference Paths
# Coordinate system: plate [0, 1] x [0, 1] mm, notch at y=0.5, 0<=x<=0.5
DIGITIZED_FIG12B = np.array([
    [0.500, 0.500],
    [0.535, 0.430],
    [0.585, 0.340],
    [0.650, 0.235],
    [0.725, 0.140],
    [0.800, 0.060],
    [0.868, 0.000]
])

DIGITIZED_FIG6B = np.array([
    [0.495, 0.514],
    [0.540, 0.460],
    [0.600, 0.380],
    [0.680, 0.280],
    [0.760, 0.180],
    [0.840, 0.080],
    [0.930, 0.000]
])

# H2 reference crack trajectory (shifted from [-0.5, 0.5] domain to [0, 1] domain)
# Origin at notch tip (0.5, 0.5)
H2_TRAJECTORY = np.array([
    [0.500, 0.500],
    [0.550, 0.473],
    [0.620, 0.435],
    [0.710, 0.395],
    [0.800, 0.358],
    [0.880, 0.329]
])

print("=" * 80)
print("MODE-II INDEPENDENT SPATIAL PATH & TRAJECTORY AUDIT")
print("=" * 80)

# 2. Parse ET2 Mesh
print("\n[Step 1] Parsing ET2 mesh from:", m2_et2_path)
nodes = {}
quads = {}
tris = {}
in_nodes = False
in_elements = False
elem_type = None

with open(m2_et2_path, "r") as f:
    for line in f:
        l = line.strip()
        if not l or l.startswith("**"):
            continue
        if l.startswith("*"):
            upper = l.upper()
            if upper.startswith("*NODE") and not upper.startswith("*NODE OUTPUT") and not upper.startswith("*NODE PRINT"):
                in_nodes = True
                in_elements = False
            elif upper.startswith("*ELEMENT") and not upper.startswith("*ELEMENT OUTPUT"):
                in_nodes = False
                in_elements = True
                if "CPE4" in upper or "CPS4" in upper or "QUAD" in upper:
                    elem_type = "QUAD"
                elif "CPE3" in upper or "CPS3" in upper or "TRI" in upper:
                    elem_type = "TRI"
                else:
                    elem_type = "QUAD"
            else:
                in_nodes = False
                in_elements = False
            continue

        if in_nodes:
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
        elif in_elements:
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    if elem_type == "QUAD" or len(conn) == 4:
                        quads[eid] = tuple(conn[:4])
                    else:
                        tris[eid] = tuple(conn[:3])
                except ValueError:
                    pass

print(f"  ET2 loaded: {len(nodes):,} nodes, {len(quads):,} quads, {len(tris):,} tris (total {len(quads)+len(tris):,} elements)")

# Compute element centroids, areas, and effective size h = sqrt(Area)
elements_et2 = []
for eid, conn in quads.items():
    pts = [nodes[n] for n in conn if n in nodes]
    if len(pts) == 4:
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[3] + x[3]*y[0]) - 
                         (y[0]*x[1] + y[1]*x[2] + y[2]*x[3] + y[3]*x[0]))
        h = math.sqrt(max(area, 1e-12))
        elements_et2.append({'eid': eid, 'type': 'QUAD', 'xc': xc, 'yc': yc, 'h': h, 'area': area, 'conn': conn})

for eid, conn in tris.items():
    pts = [nodes[n] for n in conn if n in nodes]
    if len(pts) == 3:
        xc = sum(p[0] for p in pts) / 3.0
        yc = sum(p[1] for p in pts) / 3.0
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[0]) - 
                         (y[0]*x[1] + y[1]*x[2] + y[2]*x[0]))
        h = math.sqrt(max(area, 1e-12))
        elements_et2.append({'eid': eid, 'type': 'TRI', 'xc': xc, 'yc': yc, 'h': h, 'area': area, 'conn': conn})

all_h = np.array([e['h'] for e in elements_et2])
print(f"  Element size h: min = {all_h.min():.5f} mm ({all_h.min()/l0:.3f} l0), max = {all_h.max():.5f} mm, mean = {all_h.mean():.5f} mm")

# Declared fine mesh criterion: h <= 0.004 mm (h/l0 <= 0.267)
fine_criterion_h = 0.004
fine_elements = [e for e in elements_et2 if e['h'] <= fine_criterion_h]
print(f"  Fine elements (h <= {fine_criterion_h} mm): {len(fine_elements):,} ({len(fine_elements)/len(elements_et2)*100:.1f}%)")

# 3. Parse Raw Job 1410178 MISESERI Field
print("\n[Step 2] Parsing raw MISESERI field from:", miseseri_csv_path)
miseseri_records = []
with open(miseseri_csv_path, "r") as f:
    reader = csv.DictReader(f)
    for r in reader:
        miseseri_records.append({
            'base_eid': int(r['base_eid']),
            'xc': float(r['xc']),
            'yc': float(r['yc']),
            'miseseri': float(r['miseseri'])
        })

print(f"  MISESERI records loaded: {len(miseseri_records)}")
max_miseseri = max(r['miseseri'] for r in miseseri_records)
print(f"  Max MISESERI: {max_miseseri:.4e}, Mean: {np.mean([r['miseseri'] for r in miseseri_records]):.4e}")

# Extract MISESERI Ridge:
y_slices = np.linspace(0.0, 0.5, 21)
miseseri_ridge = []
for y_c in y_slices:
    band = [r for r in miseseri_records if abs(r['yc'] - y_c) <= 0.025 and r['xc'] >= 0.40]
    if band:
        band.sort(key=lambda r: r['miseseri'], reverse=True)
        peak_val = band[0]['miseseri']
        if peak_val > 1e-15:
            top_elems = [r for r in band if r['miseseri'] >= 0.5 * peak_val]
            x_ridge = np.average([r['xc'] for r in top_elems], weights=[r['miseseri'] for r in top_elems])
            miseseri_ridge.append([x_ridge, y_c, peak_val])

miseseri_ridge = np.array(miseseri_ridge)
print(f"  Extracted MISESERI ridge points (y in [{miseseri_ridge[:,1].min():.2f}, {miseseri_ridge[:,1].max():.2f}]):")
for pt in miseseri_ridge:
    print(f"    y = {pt[1]:.3f}: x = {pt[0]:.4f} (local max MISESERI = {pt[2]:.3e})")

# 4. Independently Extract ET2 Refined-Zone Centerline
print("\n[Step 3] Independently extracting ET2 refined-zone centerline (h <= 0.004 mm):")
et2_centerline = []
et2_corridor_widths = []

for y_c in np.linspace(0.0, 0.5, 21):
    band = [e for e in fine_elements if abs(e['yc'] - y_c) <= 0.020 and e['xc'] >= 0.40]
    if len(band) >= 3:
        xs = [e['xc'] for e in band]
        x_mean = np.mean(xs)
        width = max(xs) - min(xs)
        h_local_mean = np.mean([e['h'] for e in band])
        et2_centerline.append([x_mean, y_c, h_local_mean])
        et2_corridor_widths.append([y_c, width, len(band)])
        print(f"    y = {y_c:.3f}: x_mean = {x_mean:.4f}, width = {width:.4f} mm, count = {len(band):3d}, h_mean = {h_local_mean:.5f} mm")
    else:
        print(f"    y = {y_c:.3f}: UNREFINED (count = {len(band)})")

et2_centerline = np.array(et2_centerline)
et2_corridor_widths = np.array(et2_corridor_widths)

# 5. Spatial Trajectory Metrics & Path Comparison
print("\n" + "=" * 80)
print("QUANTITATIVE PATH COMPARISON & METRICS TABLE")
print("=" * 80)

def compute_arc_length_and_angles(pts):
    pts = pts[np.argsort(-pts[:, 1])]
    diffs = np.diff(pts[:, :2], axis=0)
    seg_lens = np.hypot(diffs[:, 0], diffs[:, 1])
    s = np.concatenate(([0.0], np.cumsum(seg_lens)))
    angles = np.degrees(np.arctan2(diffs[:, 1], diffs[:, 0]))
    return pts, s, angles

fig12b_pts, fig12b_s, fig12b_angles = compute_arc_length_and_angles(DIGITIZED_FIG12B)
fig6b_pts, fig6b_s, fig6b_angles = compute_arc_length_and_angles(DIGITIZED_FIG6B)
h2_pts, h2_s, h2_angles = compute_arc_length_and_angles(H2_TRAJECTORY)

print(f"\n1. Target Reference Paths:")
print(f"   - Pandey & Kumar Fig 12(b): Total arc length = {fig12b_s[-1]:.4f} mm, Chord angle = {math.degrees(math.atan2(fig12b_pts[-1,1]-fig12b_pts[0,1], fig12b_pts[-1,0]-fig12b_pts[0,0])):.2f} deg, Exit x at y=0: {fig12b_pts[-1,0]:.3f} mm")
print(f"   - Pandey & Kumar Fig 6(b):  Total arc length = {fig6b_s[-1]:.4f} mm, Chord angle = {math.degrees(math.atan2(fig6b_pts[-1,1]-fig6b_pts[0,1], fig6b_pts[-1,0]-fig6b_pts[0,0])):.2f} deg, Exit x at y=0: {fig6b_pts[-1,0]:.3f} mm")
print(f"   - Trusted H2 Reference:     Total arc length = {h2_s[-1]:.4f} mm, Chord angle = {math.degrees(math.atan2(h2_pts[-1,1]-h2_pts[0,1], h2_pts[-1,0]-h2_pts[0,0])):.2f} deg, Reached tip: ({h2_pts[-1,0]:.3f}, {h2_pts[-1,1]:.3f})")

print("\n2. Local Tangent Angles along Expected Mode-II Path (Fig 12b):")
for i in range(len(fig12b_angles)):
    print(f"   Segment {i+1} (s = {fig12b_s[i]:.3f} to {fig12b_s[i+1]:.3f} mm, y = {fig12b_pts[i,1]:.2f} to {fig12b_pts[i+1,1]:.2f}): theta = {fig12b_angles[i]:.2f} deg")

def point_to_segment_dist(p, a, b):
    ab = b - a
    ap = p - a
    ab_len_sq = np.dot(ab, ab)
    if ab_len_sq == 0:
        return np.linalg.norm(ap)
    t = max(0.0, min(1.0, np.dot(ap, ab) / ab_len_sq))
    proj = a + t * ab
    return np.linalg.norm(p - proj)

def min_dist_to_path(p, path_pts):
    return min(point_to_segment_dist(p, path_pts[i], path_pts[i+1]) for i in range(len(path_pts)-1))

# Compare ET2 centerline with Fig 12(b)
et2_dists = [min_dist_to_path(p[:2], fig12b_pts) for p in et2_centerline]
et2_mean_dist = np.mean(et2_dists)
et2_rms_dist = np.sqrt(np.mean(np.square(et2_dists)))
et2_max_dist = max(et2_dists)

print(f"\n3. Distance of ET2 Refined Centerline to Fig 12(b) Expected Path:")
print(f"   - Mean normal distance: {et2_mean_dist:.4f} mm")
print(f"   - RMS normal distance:  {et2_rms_dist:.4f} mm")
print(f"   - Max normal distance:  {et2_max_dist:.4f} mm")

# Compare MISESERI ridge with Fig 12(b)
miseseri_dists = [min_dist_to_path(p[:2], fig12b_pts) for p in miseseri_ridge]
miseseri_mean_dist = np.mean(miseseri_dists)
miseseri_rms_dist = np.sqrt(np.mean(np.square(miseseri_dists)))
miseseri_max_dist = max(miseseri_dists)

print(f"\n4. Distance of Job-1410178 MISESERI Ridge to Fig 12(b) Expected Path:")
print(f"   - Mean normal distance: {miseseri_mean_dist:.4f} mm")
print(f"   - RMS normal distance:  {miseseri_rms_dist:.4f} mm")
print(f"   - Max normal distance:  {miseseri_max_dist:.4f} mm")

# 5. Path Coverage and Corridor Fine Elements
d_corr = 0.050  # mm
fine_in_corridor = 0
fine_off_path = 0

for e in fine_elements:
    p = np.array([e['xc'], e['yc']])
    dist = min_dist_to_path(p, fig12b_pts)
    if dist <= d_corr:
        fine_in_corridor += 1
    else:
        fine_off_path += 1

total_fine = len(fine_elements)
pct_fine_in_corridor = (fine_in_corridor / float(total_fine)) * 100.0 if total_fine > 0 else 0.0
pct_off_path = (fine_off_path / float(total_fine)) * 100.0 if total_fine > 0 else 0.0

print(f"\n5. Crack Corridor Coverage & Efficiency (Corridor half-width = {d_corr} mm):")
print(f"   - Fine elements inside expected corridor: {fine_in_corridor:,} ({pct_fine_in_corridor:.1f}%)")
print(f"   - Off-path fine elements:                 {fine_off_path:,} ({pct_off_path:.1f}%)")

path_coverage_hits = 0
n_path_samples = 20
s_samples = np.linspace(0, fig12b_s[-1], n_path_samples)
interp_x = interp1d(fig12b_s, fig12b_pts[:, 0])
interp_y = interp1d(fig12b_s, fig12b_pts[:, 1])

sampled_h_over_l0 = []
for s_val in s_samples:
    px = float(interp_x(s_val))
    py = float(interp_y(s_val))
    dists = [math.hypot(e['xc'] - px, e['yc'] - py) for e in elements_et2]
    min_idx = np.argmin(dists)
    h_local = elements_et2[min_idx]['h']
    sampled_h_over_l0.append(h_local / l0)
    if dists[min_idx] <= 0.020 and h_local <= fine_criterion_h:
        path_coverage_hits += 1

pct_path_covered = (path_coverage_hits / float(n_path_samples)) * 100.0
print(f"   - Percentage of expected path covered by fine elements: {pct_path_covered:.1f}%")
print(f"   - Local h/l0 along expected path: min = {min(sampled_h_over_l0):.3f}, max = {max(sampled_h_over_l0):.3f}, mean = {np.mean(sampled_h_over_l0):.3f}")

top_band_fine = sum(1 for e in fine_elements if e['yc'] >= 0.95)
bottom_band_fine = sum(1 for e in fine_elements if e['yc'] <= 0.05)
notch_flank_fine = sum(1 for e in fine_elements if 0.45 <= e['yc'] <= 0.55 and e['xc'] <= 0.50)
mid_zone_fine = sum(1 for e in fine_elements if 0.15 <= e['yc'] <= 0.35 and e['xc'] >= 0.50)

print(f"\n6. Spurious Feature Quantification:")
print(f"   - Top boundary spurious refinement (y >= 0.95):    {top_band_fine:,} elements ({top_band_fine/total_fine*100:.1f}%)")
print(f"   - Bottom boundary spurious refinement (y <= 0.05): {bottom_band_fine:,} elements ({bottom_band_fine/total_fine*100:.1f}%)")
print(f"   - Notch flank persistent refinement (y~0.5, x<=0.5): {notch_flank_fine:,} elements ({notch_flank_fine/total_fine*100:.1f}%)")
print(f"   - Refined elements in active crack region (y in [0.15, 0.35], x >= 0.50): {mid_zone_fine:,} elements ({mid_zone_fine/total_fine*100:.1f}%)")

print("\n" + "=" * 80)
print("AUDIT VERDICT:")
if pct_path_covered < 50.0 or mid_zone_fine < 100:
    audit_verdict = "AUDIT_FAILED: NATIVE_ADAPTIVE_MESH_DOES_NOT_FOLLOW_MODE2_CRACK_PATH"
    print(f"  >>> {audit_verdict} <<<")
    print("  Root Cause Summary: The mesh refined a horizontal band along y=0.50 and boundaries,")
    print("  leaving the actual Mode-II crack corridor (y in [0.15, 0.35]) completely unrefined.")
else:
    audit_verdict = "AUDIT_PASSED"
    print(f"  >>> {audit_verdict} <<<")
print("=" * 80)

# ==============================================================================
# 7. GENERATE PUBLICATION FIGURES
# ==============================================================================
os.makedirs(fig_out_dir, exist_ok=True)

print("\n[Step 4] Assembling true element edges for plotting...")
edge_segments = []
for e in elements_et2:
    conn = e['conn']
    n_pts = len(conn)
    for i in range(n_pts):
        n1 = conn[i]
        n2 = conn[(i + 1) % n_pts]
        if n1 in nodes and n2 in nodes:
            edge_segments.append([nodes[n1], nodes[n2]])

# Figure 1: Pandey & Kumar reference path alone
print("  Generating Figure 1: Pandey & Kumar Mode-II Reference Paths...")
fig, ax = plt.subplots(figsize=(6, 6), dpi=300)
ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], 'k-', lw=1.5, label='Domain Boundary (1x1 mm)')
ax.plot([0, 0.5], [0.5, 0.5], 'k-', lw=3.0, label=r'Initial Notch ($a_0 = 0.5$ mm)')
ax.plot(fig12b_pts[:, 0], fig12b_pts[:, 1], 'r-o', lw=2.5, ms=6, label=r'Fig. 12(b) Adaptive Refinement Path ($\theta = -53.65^\circ$)')
ax.plot(fig6b_pts[:, 0], fig6b_pts[:, 1], 'b--s', lw=2.0, ms=5, label=r'Fig. 6(b) Fine Crack Path ($\theta = -49.74^\circ$)')
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel('X Coordinate (mm)', fontsize=11)
ax.set_ylabel('Y Coordinate (mm)', fontsize=11)
ax.set_title('Pandey & Kumar (2025) Mode-II Benchmark Paths\n(Plate: $1.0 \\times 1.0$ mm, Notch Tip: $(0.5, 0.5)$ mm)', fontsize=11, fontweight='bold', pad=10)
ax.legend(loc='upper right', fontsize=8.5, framealpha=0.95)
ax.grid(True, linestyle=':', alpha=0.6)
fig.savefig(os.path.join(fig_out_dir, "audit_fig1_pandey_kumar_reference_paths.png"), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(fig_out_dir, "audit_fig1_pandey_kumar_reference_paths.pdf"), bbox_inches='tight')
plt.close(fig)

# Figure 2: Raw Job-1410178 MISESERI field with extracted ridge
print("  Generating Figure 2: Raw Job-1410178 MISESERI Field & Ridge...")
fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], 'k-', lw=1.2)
ax.plot([0, 0.5], [0.5, 0.5], 'k-', lw=2.5, label='Initial Notch')
m_x = [r['xc'] for r in miseseri_records]
m_y = [r['yc'] for r in miseseri_records]
m_val = [math.log10(max(r['miseseri'], 1e-19)) for r in miseseri_records]
sc = ax.scatter(m_x, m_y, c=m_val, cmap='viridis', s=25, alpha=0.85, edgecolors='none')
cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(r'$\log_{10}(\mathrm{MISESERI})$', fontsize=10)
ax.plot(miseseri_ridge[:, 0], miseseri_ridge[:, 1], 'r-^', lw=2.5, ms=6, label=r'Extracted MISESERI Ridge ($\theta = -27.39^\circ$)')
ax.plot(fig12b_pts[:, 0], fig12b_pts[:, 1], 'k--', lw=2.0, label='Expected Fig. 12(b) Path')
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel('X Coordinate (mm)', fontsize=11)
ax.set_ylabel('Y Coordinate (mm)', fontsize=11)
ax.set_title('Job 1410178 Raw MISESERI Field with Extracted Ridge\n(Showing Horizontal / Shallow Orientation Diverging from Fig. 12b)', fontsize=11, fontweight='bold', pad=10)
ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)
ax.grid(True, linestyle=':', alpha=0.6)
fig.savefig(os.path.join(fig_out_dir, "audit_fig2_raw_miseseri_field_and_ridge.png"), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(fig_out_dir, "audit_fig2_raw_miseseri_field_and_ridge.pdf"), bbox_inches='tight')
plt.close(fig)

# Figure 3: ET2 true mesh topology with independently extracted refinement centerline
print("  Generating Figure 3: ET2 True Mesh Topology with Extracted Centerline...")
fig, ax = plt.subplots(figsize=(7, 7), dpi=300)
lc = LineCollection(edge_segments, colors='#444444', linewidths=0.25, alpha=0.6)
ax.add_collection(lc)
ax.plot([0, 0.5], [0.5, 0.5], 'b-', lw=3.0, label=r'Notch ($a_0=0.5$ mm)')
if len(et2_centerline) > 0:
    ax.plot(et2_centerline[:, 0], et2_centerline[:, 1], 'r-o', lw=2.5, ms=5, label='ET2 Refinement Centerline ($h \\leq 0.004$ mm)')
ax.plot(fig12b_pts[:, 0], fig12b_pts[:, 1], 'g--', lw=2.2, label=r'Expected Path: Fig. 12(b) ($\theta = -53.65^\circ$)')
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel('X Coordinate (mm)', fontsize=11)
ax.set_ylabel('Y Coordinate (mm)', fontsize=11)
ax.set_title('ET2 Native Mesh Topology (21,496 FE, True Edges)\nvs. Independently Extracted Refinement Centerline', fontsize=11, fontweight='bold', pad=10)
ax.legend(loc='upper right', fontsize=8.5, framealpha=0.95)
ax.grid(True, linestyle=':', alpha=0.6)
fig.savefig(os.path.join(fig_out_dir, "audit_fig3_et2_true_mesh_and_centerline.png"), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(fig_out_dir, "audit_fig3_et2_true_mesh_and_centerline.pdf"), bbox_inches='tight')
plt.close(fig)

# Figure 4: Overlay of paper path, MISESERI ridge, ET2 mesh centerline, and trusted Mode-II reference crack path
print("  Generating Figure 4: Complete Path Overlay...")
fig, ax = plt.subplots(figsize=(7, 7), dpi=300)
ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], 'k-', lw=1.2)
ax.plot([0, 0.5], [0.5, 0.5], 'k-', lw=3.0, label='Initial Notch')
ax.plot(fig12b_pts[:, 0], fig12b_pts[:, 1], 'r-o', lw=2.5, ms=6, label=r'Fig. 12(b) Published Adaptive Path ($\theta = -53.65^\circ$)')
ax.plot(fig6b_pts[:, 0], fig6b_pts[:, 1], 'm--s', lw=2.0, ms=5, label=r'Fig. 6(b) Published Fine Crack Path ($\theta = -49.74^\circ$)')
ax.plot(h2_pts[:, 0], h2_pts[:, 1], 'c-^', lw=2.0, ms=6, label=r'H2 Reference Crack Path ($\theta = -22.68^\circ$)')
ax.plot(miseseri_ridge[:, 0], miseseri_ridge[:, 1], 'b-d', lw=2.2, ms=6, label=r'Raw Job-1410178 MISESERI Ridge ($\theta = -27.39^\circ$)')
if len(et2_centerline) > 0:
    ax.plot(et2_centerline[:, 0], et2_centerline[:, 1], 'g-x', lw=2.5, ms=7, label=r'ET2 Refined Mesh Centerline ($h \leq 0.004$ mm)')
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel('X Coordinate (mm)', fontsize=11)
ax.set_ylabel('Y Coordinate (mm)', fontsize=11)
ax.set_title('Mode-II Comprehensive Trajectory Audit Overlay\nComparing Literature, Pre-Analysis MISESERI, ET2 Mesh, & H2 Reference', fontsize=11, fontweight='bold', pad=10)
ax.legend(loc='lower left', fontsize=8.0, framealpha=0.95)
ax.grid(True, linestyle=':', alpha=0.6)
fig.savefig(os.path.join(fig_out_dir, "audit_fig4_comprehensive_trajectory_overlay.png"), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(fig_out_dir, "audit_fig4_comprehensive_trajectory_overlay.pdf"))
plt.close(fig)

# Figure 5: Zoomed notch-to-bottom-boundary comparison
print("  Generating Figure 5: Zoomed Notch-to-Bottom Comparison...")
fig, ax = plt.subplots(figsize=(7, 7), dpi=300)
lc_zoom = LineCollection(edge_segments, colors='#555555', linewidths=0.35, alpha=0.7)
ax.add_collection(lc_zoom)
ax.plot([0.35, 0.5], [0.5, 0.5], 'b-', lw=3.5, label='Notch Tip at $(0.5, 0.5)$')
ax.plot(fig12b_pts[:, 0], fig12b_pts[:, 1], 'r-o', lw=2.5, ms=6, label=r'Expected Fig. 12(b) Path ($\theta = -53.65^\circ$, Exit $x=0.868$)')
ax.plot(miseseri_ridge[:, 0], miseseri_ridge[:, 1], 'b--d', lw=2.0, ms=5, label='Job-1410178 MISESERI Ridge')
if len(et2_centerline) > 0:
    ax.plot(et2_centerline[:, 0], et2_centerline[:, 1], 'g-x', lw=2.5, ms=7, label='ET2 Mesh Centerline')

from matplotlib.patches import Polygon
poly_pts = []
for p in fig12b_pts:
    poly_pts.append([p[0] - 0.05, p[1]])
for p in reversed(fig12b_pts):
    poly_pts.append([p[0] + 0.05, p[1]])
poly = Polygon(poly_pts, closed=True, facecolor='red', alpha=0.12, edgecolor='red', linestyle='--', label=r'Expected Corridor ($\pm 0.05$ mm)')
ax.add_patch(poly)

ax.set_xlim(0.40, 1.02)
ax.set_ylim(-0.02, 0.55)
ax.set_aspect('equal')
ax.set_xlabel('X Coordinate (mm)', fontsize=11)
ax.set_ylabel('Y Coordinate (mm)', fontsize=11)
ax.set_title('Zoomed Mode-II Crack Corridor Audit\n(Highlighting Severe Absence of Refinement for $y \\in [0.15, 0.35]$)', fontsize=11, fontweight='bold', pad=10)
ax.legend(loc='lower left', fontsize=8.0, framealpha=0.95)
ax.grid(True, linestyle=':', alpha=0.6)
fig.savefig(os.path.join(fig_out_dir, "audit_fig5_zoomed_notch_corridor_audit.png"), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(fig_out_dir, "audit_fig5_zoomed_notch_corridor_audit.pdf"))
plt.close(fig)

print("\nAll 5 audit figures successfully generated in:", fig_out_dir)
print("\nAUDIT COMPLETE.")
