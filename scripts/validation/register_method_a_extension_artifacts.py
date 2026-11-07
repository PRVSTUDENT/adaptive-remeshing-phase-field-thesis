# -*- coding: utf-8 -*-
"""Register Method A Localized Extension artifacts in ARTIFACT_REGISTRY.csv."""
import hashlib
import os

files = [
    ("deck-method-a-ext-phys", "Mode-I", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_PHYS.inp", "INPUT_DECK", "READY", "gemini-antigravity", "a561a89e", "Damage-informed localized Method A physical mesh (23,664 elements)"),
    ("deck-method-a-ext-uel", "Mode-I", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_PROD.inp", "INPUT_DECK", "READY", "gemini-antigravity", "a561a89e", "Damage-informed localized Method A 3-layer UEL production deck (70,992 elements)"),
    ("script-method-a-ext-generator", "Mode-I", "scripts/remeshing/generate_damage_informed_method_a_mesh.py", "SCRIPT", "READY", "gemini-antigravity", "a561a89e", "Damage-informed localized Method A mesh generator"),
    ("script-method-a-ext-audit", "Mode-I", "scripts/validation/validate_method_a_localized_extension_mesh.py", "SCRIPT", "READY", "gemini-antigravity", "a561a89e", "Quantitative validator for localized Method A extension"),
    ("script-method-a-ext-plots", "Mode-I", "scripts/visualization/plot_method_a_localized_extension_figures.py", "SCRIPT", "READY", "gemini-antigravity", "a561a89e", "Publication figures generator for localized Method A extension"),
    ("val-method-a-ext-audit-json", "Mode-I", "results/validation/method_a_localized_extension_audit.json", "DATA", "READY", "gemini-antigravity", "a561a89e", "Quantitative audit metrics for localized Method A extension"),
    ("val-method-a-ext-audit-md", "Mode-I", "results/validation/method_a_localized_extension_audit.md", "REPORT", "READY", "gemini-antigravity", "a561a89e", "Scientific evaluation report for localized Method A extension"),
    ("fig-method-a-ext-full-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_localized_extension_full_mesh.png", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Full plate localized Method A mesh PNG"),
    ("fig-method-a-ext-full-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_localized_extension_full_mesh.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Full plate localized Method A mesh PDF"),
    ("fig-method-a-ext-zoom-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_localized_extension_zoom_mesh.png", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Zoomed FPZ localized Method A mesh PNG"),
    ("fig-method-a-ext-zoom-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_localized_extension_zoom_mesh.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Zoomed FPZ localized Method A mesh PDF"),
    ("fig-method-a-ext-compare-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_native_vs_localized_comparison.png", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Side-by-side native vs localized mesh comparison PNG"),
    ("fig-method-a-ext-compare-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_native_vs_localized_comparison.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Side-by-side native vs localized mesh comparison PDF"),
    ("fig-method-a-ext-overlay-png", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_indicator_support_overlay.png", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Precritical indicator support overlay with adapted mesh size PNG"),
    ("fig-method-a-ext-overlay-pdf", "Mode-I", "MA_AdaptiveRemeshing_Report_2026/figures/fig_method_a_indicator_support_overlay.pdf", "FIGURE", "VALIDATED", "gemini-antigravity", "a561a89e", "Precritical indicator support overlay with adapted mesh size PDF")
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
