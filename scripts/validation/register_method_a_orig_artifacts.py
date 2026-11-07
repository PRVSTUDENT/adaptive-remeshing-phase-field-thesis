# -*- coding: utf-8 -*-
"""Register Method A Original Framework artifacts in ARTIFACT_REGISTRY.csv."""
import hashlib
import os

files = [
    ("deck-method-a-orig-phys", "Mode-I", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_ORIG_METHOD_A_PROD_PHYS.inp", "INPUT_DECK", "READY", "gemini-antigravity", "417c13d9", "Authentic native Method A adapted physical mesh 46747 elements"),
    ("deck-method-a-orig-uel", "Mode-I", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_ORIG_METHOD_A_PROD.inp", "INPUT_DECK", "READY", "gemini-antigravity", "417c13d9", "Authentic native Method A layered UEL production deck 140241 elements"),
    ("val-method-a-preanalysis-miseseri-csv", "Mode-I", "results/validation/method_a_preanalysis_miseseri_field.csv", "DATA", "READY", "gemini-antigravity", "417c13d9", "Authentic preanalysis MISESERI element field for 2906 elements"),
    ("val-method-a-orig-audit-json", "Mode-I", "results/validation/method_a_original_framework_audit.json", "DATA", "READY", "gemini-antigravity", "417c13d9", "Method A original framework quantitative audit and selectivity metrics"),
    ("val-method-a-orig-audit-md", "Mode-I", "results/validation/method_a_original_framework_audit.md", "REPORT", "READY", "gemini-antigravity", "417c13d9", "Method A original framework scientific evaluation and diagnosis report"),
    ("script-method-a-orig-validation", "Mode-I", "scripts/validation/validate_method_a_original_framework_mesh.py", "SCRIPT", "READY", "gemini-antigravity", "417c13d9", "Quantitative validator and selectivity auditor for original Method A"),
    ("script-method-a-orig-plotting", "Mode-I", "scripts/visualization/plot_method_a_original_framework_figures.py", "SCRIPT", "READY", "gemini-antigravity", "417c13d9", "Publication figures generator for original Method A adapted mesh"),
    ("fig-method-a-orig-full-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_original_framework_full_mesh.png", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Full 1x1 mm plate original Method A adapted mesh PNG"),
    ("fig-method-a-orig-full-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_original_framework_full_mesh.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Full 1x1 mm plate original Method A adapted mesh PDF"),
    ("fig-method-a-orig-zoom-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_original_framework_zoom_mesh.png", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Zoomed fracture process zone original Method A adapted mesh PNG"),
    ("fig-method-a-orig-zoom-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_original_framework_zoom_mesh.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Zoomed fracture process zone original Method A adapted mesh PDF"),
    ("fig-method-a-orig-compare-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_original_vs_native_adapted.png", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Side-by-side coarse vs native adapted mesh PNG"),
    ("fig-method-a-orig-compare-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_original_vs_native_adapted.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Side-by-side coarse vs native adapted mesh PDF"),
    ("fig-method-a-orig-corr-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_miseseri_refinement_correlation.png", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Preanalysis MISESERI vs adapted element size correlation PNG"),
    ("fig-method-a-orig-corr-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_miseseri_refinement_correlation.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "417c13d9", "Preanalysis MISESERI vs adapted element size correlation PDF")
]

rows = []
for name, domain, path, kind, status, agent, commit, desc in files:
    with open(path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest().upper()
    row = f"{name},{domain},{path},{kind},{status},{agent},{commit},{sha256},,{desc}\n"
    rows.append(row)
    print(f"Registered {name}: {sha256}")

with open("project_coordination/ARTIFACT_REGISTRY.csv", "a", encoding="utf-8") as f:
    for row in rows:
        f.write(row)
print("All registered successfully to ARTIFACT_REGISTRY.csv")
