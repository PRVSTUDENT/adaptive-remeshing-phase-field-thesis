# -*- coding: utf-8 -*-
import os
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

new_artifacts = [
    ("DOC_F1736_REASSESSMENT_REPORT", "Method-A", "docs/validation/F1736_FIVE_GEOMETRY_SCIENTIFIC_REASSESSMENT_REPORT.md", "markdown_report", "Definitive scientific reassessment report auditing all five benchmark geometries and establishing acceptance matrix"),
    ("JSON_F1736_SPATIAL_AUDIT", "Method-A", "results/validation/f1736_five_case_spatial_audit.json", "json_metrics", "Quantitative element resolution h_e over ell_0 aspect ratio and Jacobian audit across all five meshes"),
    ("JSON_F1736_MESH_INVENTORY", "Method-A", "results/validation/f1736_mesh_inventory.json", "json_metrics", "Complete inventory of 182 candidate physical meshes indexed across models directory"),
    ("FIG_F1736_FIVE_CASE_CORRECTED_PNG", "Method-A", "results/figures/fig_f1736_five_case_comparison_corrected.png", "figure_png", "Corrected 5-panel comparative publication figure using authentic final meshes from Tasks F1725 F1726 F1728 F1734 and 192"),
    ("FIG_F1736_FIVE_CASE_CORRECTED_PDF", "Method-A", "results/figures/fig_f1736_five_case_comparison_corrected.pdf", "figure_pdf", "Corrected 5-panel comparative publication vector PDF figure"),
    ("FIG_F1736_CASE1_STANDALONE_PNG", "Method-A", "results/figures/fig_f1736_case_1_standalone_mesh.png", "figure_png", "Standalone high-resolution mesh wireframe and resolution distribution for Case 1 Mode I"),
    ("FIG_F1736_CASE2_STANDALONE_PNG", "Method-A", "results/figures/fig_f1736_case_2_standalone_mesh.png", "figure_png", "Standalone high-resolution mesh wireframe and resolution distribution for Case 2 Off-Axis Hole"),
    ("FIG_F1736_CASE3_STANDALONE_PNG", "Method-A", "results/figures/fig_f1736_case_3_standalone_mesh.png", "figure_png", "Standalone high-resolution mesh wireframe and resolution distribution for Case 3 Sec 4.3 Plate"),
    ("FIG_F1736_CASE4_STANDALONE_PNG", "Method-A", "results/figures/fig_f1736_case_4_standalone_mesh.png", "figure_png", "Standalone high-resolution mesh wireframe and resolution distribution for Case 4 Five Hole"),
    ("FIG_F1736_CASE5_STANDALONE_PNG", "Method-A", "results/figures/fig_f1736_case_5_standalone_mesh.png", "figure_png", "Standalone high-resolution mesh wireframe and resolution distribution for Case 5 Seven Hole"),
    ("PY_AUDIT_F1736_SPATIAL", "Method-A", "scripts/remeshing/audit_f1736_spatial_resolution.py", "python_script", "Script computing quantitative spatial resolution Jacobians and compliance across 5 meshes"),
    ("PY_PLOT_F1736_MESHES", "Method-A", "scripts/remeshing/plot_f1736_meshes.py", "python_script", "High-resolution publication plotting script generating standalone and 5-panel figures"),
    ("PY_TEST_F1736_SPATIAL", "Method-A", "tests/unit/test_f1736_spatial_resolution.py", "python_test", "Unit test asserting zero negative Jacobians quad compliance and correct element counts"),
    ("PY_TEST_F1736_FIGURES", "Method-A", "tests/unit/test_f1736_figures.py", "python_test", "Unit test verifying generation and non-zero byte size of all F1736 figures")
]

def main():
    reg_path = os.path.join(REPO_ROOT, "project_coordination", "ARTIFACT_REGISTRY.csv")
    with open(reg_path, "r", encoding="utf-8") as f:
        existing = f.read()

    lines = []
    for aid, stage, rel, atype, notes in new_artifacts:
        full = os.path.join(REPO_ROOT, rel)
        if aid in existing:
            print(f"Artifact {aid} already registered, skipping.")
            continue
        h = hashlib.sha256()
        with open(full, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        sha = h.hexdigest().upper()
        lines.append(f"{aid},{stage},{rel},{atype},pass,gemini-antigravity,HEAD,{sha},,{notes}\n")

    if lines:
        with open(reg_path, "a", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Appended {len(lines)} new artifacts to ARTIFACT_REGISTRY.csv")
    else:
        print("No new artifacts needed to be appended.")

if __name__ == "__main__":
    main()
