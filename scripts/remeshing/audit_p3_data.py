# -*- coding: utf-8 -*-
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
P3_DIR = REPO_ROOT / "models" / "complex_mixed_load" / "campaign_results"
NOVEL_DIR = REPO_ROOT / "models" / "novel_inclined_notch_hole" / "campaign_results_narrow_band"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

p3_files = [P3_DIR / "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_SUMMARY.json"] + [
    P3_DIR / f"PK_METHOD_C_MIXED_LOAD_CYCLE{c}_SUMMARY.json" for c in range(1, 9)
]

def print_out(msg):
    with open(REPO_ROOT / "audit_output.txt", "a", encoding="utf-8") as out:
        out.write(str(msg) + "\n")

# Clear file
with open(REPO_ROOT / "audit_output.txt", "w", encoding="utf-8") as out:
    out.write("")

print_out("=== PROBLEM 3 SUMMARY DATA ===")
max_sdv17_jump = -1e9
min_sdv18_jump = 1e9

for i, f in enumerate(p3_files):
    d = json.loads(f.read_text(encoding="utf-8"))
    c = d.get("cycle", 0)
    job = d.get("job_name")
    uy = d.get("terminal_uy_mm")
    ux = d.get("terminal_ux_mm")
    rf2 = d.get("terminal_rf2_kn")
    rf1 = d.get("terminal_rf1_kn")
    peak_rf2 = d.get("peak_rf2_kn")
    peak_rf1 = d.get("peak_rf1_kn")
    tip = d.get("tip_mm")
    chord = d.get("tip_history_chord_sum_mm")
    dist_h = d.get("dist_to_hole_boundary_mm")
    dmax = d.get("max_damage")
    elems = d.get("mesh_elements")
    nodes = d.get("mesh_nodes")
    gr = d.get("gate_results", {})
    drf2 = gr.get("delta_rf2_pct")
    drf1 = gr.get("delta_rf1_pct")
    ds17 = gr.get("delta_sdv17_pct")
    ds18 = gr.get("delta_sdv18_pct")
    f_sha = sha256_file(f)
    donor_ckpt = d.get("donor_checkpoint_sha256")
    mesh_sha = d.get("mesh_sha256")
    
    if ds17 is not None and ds17 > max_sdv17_jump:
        max_sdv17_jump = ds17
    if ds18 is not None and ds18 < min_sdv18_jump:
        min_sdv18_jump = ds18
        
    print_out(f"Cycle {c}:")
    print_out(f"  Job: {job}")
    print_out(f"  Summary File SHA: {f_sha}")
    print_out(f"  Mesh SHA: {mesh_sha}")
    print_out(f"  Donor Checkpoint SHA: {donor_ckpt}")
    print_out(f"  uy: {uy:.6f} mm, ux: {ux:.6f} mm")
    print_out(f"  RF2: {rf2:.6f} kN, RF1: {rf1:.6f} kN")
    print_out(f"  peak_rf2: {peak_rf2:.6f} kN, peak_rf1: {peak_rf1:.6f} kN")
    print_out(f"  d_max: {dmax:.6f}")
    print_out(f"  tip: [{tip[0]:.6f}, {tip[1]:.6f}]")
    print_out(f"  chord sum: {chord:.6f} mm")
    print_out(f"  dist_to_hole: {dist_h:.6e} mm")
    print_out(f"  elements: {elems}, nodes: {nodes}")
    print_out(f"  Delta RF2: {drf2}%")
    print_out(f"  Delta RF1: {drf1}%")
    print_out(f"  Delta SDV17: {ds17}%")
    print_out(f"  Delta SDV18: {ds18}%")

print_out(f"\nMax Delta SDV17 across all cycles: {max_sdv17_jump:.4f}%")
print_out(f"Min Delta SDV18 across all cycles: {min_sdv18_jump:.4f}%")

print_out("\n=== SYNTHESIS AND MEDIA FILE SHAS ===")
for name in [
    "fig_mixed_load_f_u_response.png",
    "fig_mixed_load_progression_grid.png",
    "fig_mixed_load_synthesis.png",
    "mixed_load_progression.gif",
    "image_manifest.json"
]:
    p = P3_DIR / name
    if p.exists():
        print_out(f"{name}: {sha256_file(p)} ({p.stat().st_size} bytes)")

print_out("\n=== NOVEL PURE TENSION CRACK TRAJECTORY ===")
for nc in range(10):
    nf = NOVEL_DIR / ("PK_METHOD_C_NOVEL_COARSE_JOB1_SUMMARY.json" if nc==0 else f"PK_METHOD_C_NOVEL_CYCLE{nc}_SUMMARY.json")
    if nf.exists():
        nd = json.loads(nf.read_text(encoding="utf-8"))
        ntip = nd.get("tip_mm")
        print_out(f"Novel C{nc}: tip=[{ntip[0]:.6f}, {ntip[1]:.6f}], uy={nd['terminal_uy_mm']:.6f}, RF2={nd['terminal_rf2_kn']:.4f}, chord={nd.get('tip_history_chord_sum_mm', 0):.4f}")

