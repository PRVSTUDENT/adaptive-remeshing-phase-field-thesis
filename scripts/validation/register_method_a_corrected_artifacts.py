#!/usr/bin/env python3
import os
import hashlib
import csv
from datetime import datetime

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def register_artifacts():
    now_iso = datetime.now().astimezone().isoformat()
    
    # Update TASK_LEDGER.csv
    task_row = [
        "F1651-METHOD-A-CORRECTED-LOCALIZED-MESH",
        "Mode-I",
        "Correct localized Method A mesh by removing hardcoded coordinate filter, evaluating full physical domain, and refining both notch-ligament and opposite-side hole flank supports",
        "completed",
        "gemini-antigravity",
        "1e904d07",
        "",
        "scripts/remeshing;scripts/validation;scripts/visualization;models/pandey_kumar_mode1/176_method_a_plate_with_hole;results/validation;project_coordination;MA_AdaptiveRemeshing_Report_2026",
        "",
        "CORRECTED_MESH_54563_ELEMENTS_DUAL_INDICATOR_SUPPORTS_AUDITED_FIGURES_VALIDATED",
        "STOP_FOR_USER_VISUAL_APPROVAL",
        now_iso
    ]
    
    with open("project_coordination/TASK_LEDGER.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(task_row)
    print("Registered F1651 in TASK_LEDGER.csv")

    # New artifacts to register in ARTIFACT_REGISTRY.csv
    artifacts = [
        ("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_BASELINE_PHYS.inp", "input_deck", "Preserved 23k baseline physical mesh with unrefined right flank"),
        ("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_BASELINE_PROD.inp", "input_deck", "Preserved 23k baseline layered UEL production deck"),
        ("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_CORR_PHYS.inp", "input_deck", "Corrected physical mesh with dual indicator supports (54,563 elements)"),
        ("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_CORR_PROD.inp", "input_deck", "Corrected layered UEL production deck (163,689 elements)"),
        ("results/validation/faithful_indicator_supports.json", "validation_artifact", "Authentic indicator supports polygon definitions and element components"),
        ("results/validation/method_a_corrected_localized_audit.json", "validation_artifact", "Quantitative regional audit metrics and violation identification JSON"),
        ("results/validation/method_a_corrected_localized_audit.md", "validation_artifact", "Quantitative regional audit report in Markdown"),
        ("scripts/remeshing/extract_faithful_indicator_supports.py", "script", "Script to extract faithful indicator supports without coordinate filters"),
        ("scripts/remeshing/generate_damage_informed_method_a_mesh.py", "script", "Updated damage-informed Method A extension generator with full domain evaluation"),
        ("scripts/validation/validate_method_a_corrected_localized_mesh.py", "script", "Validator script auditing longest edge compliance and violation identification"),
        ("scripts/visualization/plot_method_a_corrected_mesh_figures.py", "script", "Plotting script generating 4 publication-quality figures using Abaqus connectivity"),
        ("docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_method_a_corrected_full_mesh.png", "figure", "Full-plate corrected mesh figure (54k elements)"),
        ("docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_method_a_corrected_zoom_mesh.png", "figure", "Zoomed corrected mesh figure showing notch, hole and flanks"),
        ("docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_method_a_corrected_support_overlay.png", "figure", "Authentic indicator overlay showing full domain damage and 3*l0 buffers"),
        ("docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_method_a_baseline_vs_corrected_comparison.png", "figure", "Side-by-side comparison of baseline 23k vs corrected 54k mesh")
    ]

    with open("project_coordination/ARTIFACT_REGISTRY.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for rel_path, atype, desc in artifacts:
            if os.path.exists(rel_path):
                fhash = sha256_file(rel_path)
                fsize = os.path.getsize(rel_path)
                writer.writerow([
                    rel_path.replace("\\", "/"),
                    atype,
                    fhash,
                    fsize,
                    "gemini-antigravity",
                    "F1651-METHOD-A-CORRECTED-LOCALIZED-MESH",
                    desc,
                    now_iso
                ])
                print(f"Registered {rel_path} ({fhash[:8]}...)")
            else:
                print(f"Warning: {rel_path} does not exist")

if __name__ == '__main__':
    register_artifacts()
