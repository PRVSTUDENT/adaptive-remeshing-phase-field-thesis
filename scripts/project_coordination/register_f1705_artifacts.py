"""Register Task F1705 artifacts in ARTIFACT_REGISTRY.csv."""

import hashlib
from pathlib import Path

REGISTRY_FILE = Path("project_coordination/ARTIFACT_REGISTRY.csv")

artifacts = [
    (
        "F1705_CANDIDATE_E10_PRODUCTION_RESULTS_JSON",
        "results/validation/f1705_candidate_e10_production_results.json",
        "validation_json",
        "Comprehensive quantitative production results, parity metrics, and scaling speedup for Candidate E10"
    ),
    (
        "F1705_CANDIDATE_E10_SYNTHESIS_PNG",
        "results/validation/f1705_candidate_e10_synthesis.png",
        "figure_png",
        "Four-panel synthesis plot: load-displacement parity, energy relaxation, computational speedup, and selective refinement profile"
    ),
    (
        "F1705_CANDIDATE_E10_SYNTHESIS_PDF",
        "MA_AdaptiveRemeshing_Report_2026/figures/fig_f1705_candidate_e10_synthesis.pdf",
        "figure_pdf",
        "Vector publication figure for Chapter 5 synthesizing Candidate E10 production simulation against baseline"
    ),
    (
        "F1705_UNIT_TEST_RESULTS_SUITE",
        "tests/unit/test_f1705_candidate_e10_production_results.py",
        "test_script",
        "Unit test suite verifying Task F1705 Candidate E10 production results, parity, energy, and speedup (8/8 PASS)"
    ),
    (
        "F1705_MASTER_THESIS_PDF_BUILD",
        "MA_AdaptiveRemeshing_Report_2026/main.pdf",
        "thesis_pdf",
        "University-format Master's Thesis PDF report updated with Candidate E10 production fracture results (305 pages)"
    )
]

content = REGISTRY_FILE.read_text(encoding="utf-8")
if not content.endswith("\n"):
    content += "\n"

for key, rel_path, art_type, desc in artifacts:
    p = Path(rel_path)
    if not p.exists():
        print(f"WARNING: {rel_path} does not exist, skipping")
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    line = f'{key},Mode-I,{rel_path},{art_type},pass,gemini-antigravity,HEAD,{h},,"{desc}"\n'
    content += line
    print(f"Registered {key} ({h[:8]}...)")

REGISTRY_FILE.write_text(content, encoding="utf-8")
print("SUCCESS: ARTIFACT_REGISTRY.csv updated.")
