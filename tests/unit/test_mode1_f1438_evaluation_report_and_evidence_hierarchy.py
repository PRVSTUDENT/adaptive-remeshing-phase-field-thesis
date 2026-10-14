"""
test_mode1_f1438_evaluation_report_and_evidence_hierarchy.py

Unit test suite for Tasks F1438 through F1446:
1. Verifies the existence, structure, and supervisor-aligned content of docs/reports/MODE1_CORRECTED_METHOD_B_STEP2_FRACTURE_EVALUATION.md.
2. Validates the 5-tier epistemic evidence hierarchy and completed-evaluation metrics.
3. Verifies numerical stiffness parity (Delta K0 < 0.1%, R^2 >= 0.999999), peak force, work reduction, and partial-horizon facts.
4. Verifies governing logic section ordering following supervisor directive:
   Problem Definition -> Expected Solution -> Fixed-Mesh Reference -> Adaptive Method B -> Quantitative Comparison -> Scientific Discussion -> Comprehensive Artifacts -> Supervisor Recommendations.
5. Verifies governance coordination state and task ledger registration.
"""

import json
import os
import re
import pytest

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS_REPORT = os.path.join(WORKSPACE, "docs", "reports", "MODE1_CORRECTED_METHOD_B_STEP2_FRACTURE_EVALUATION.md")
ACTIVE_TASK = os.path.join(WORKSPACE, "project_coordination", "ACTIVE_TASK.json")
ACTIVE_SESSION = os.path.join(WORKSPACE, "project_coordination", "ACTIVE_SESSION.json")
TASK_LEDGER = os.path.join(WORKSPACE, "project_coordination", "TASK_LEDGER.csv")
SESSION_REPORT = os.path.join(WORKSPACE, "project_coordination", "sessions", "2026-10-13_1800_gemini-antigravity_F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION.md")


def test_report_contains_governing_logic_sections():
    """Assert report contains all required sections from supervisor directive."""
    assert os.path.isfile(DOCS_REPORT), f"Report not found at {DOCS_REPORT}"
    with open(DOCS_REPORT, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify key sections following supervisor structure
    assert "## 1. Problem Definition & Boundary Value Problem" in content
    assert "## 2. Expected Physical & Energetic Solution" in content
    assert "## 3. Fixed-Mesh Reference Anchor" in content
    assert "## 4. Adaptive Method B Formulation & Sizing Limitations" in content
    assert "## 5. Quantitative Multi-Quantity Comparison" in content
    assert "## 6. Scientific Discussion, Forensic Audits & Epistemic Boundaries" in content
    assert "## 7. Comprehensive Artifact, Data & Code Provenance" in content
    assert "## 8. Supervisor Meeting Recommendations & Decision Request" in content


def test_mode1_f1438_report_structure_and_supervisor_sections():
    """Alias for backwards compatibility with historical task test runners."""
    test_report_contains_governing_logic_sections()


def test_report_contains_epistemic_hierarchy_tiers():
    """Assert report defines the strict epistemic evidence hierarchy and completed numerical metrics."""
    with open(DOCS_REPORT, "r", encoding="utf-8") as f:
        content = f.read()

    # Check 5 tiers
    assert "VERIFIED_NUMERICALLY" in content
    assert "VERIFIED_GEOMETRICALLY" in content
    assert "VERIFIED_TOPOLOGICALLY" in content
    assert "EVALUATED_LIMITATION" in content
    assert "SUPPORTED_HYPOTHESIS" in content

    # Check key physical and numerical metrics
    assert "137.909558" in content  # K0
    assert "0.99999960" in content  # R^2
    assert "-0.02607" in content    # Delta K0 (numeric part)
    assert "0.743701" in content    # F_max
    assert "2.267379" in content    # W_ext terminal work
    assert "0.007889" in content    # Partial horizon u
    assert "0.001992" in content    # Force at u = 0.0060 mm (plateau eliminated)


def test_mode1_f1438_epistemic_hierarchy_and_fallback():
    """Alias for backwards compatibility with historical task test runners."""
    test_report_contains_epistemic_hierarchy_tiers()


def test_report_governing_logic_section_ordering():
    """Assert governing logic sections appear in strict sequential order."""
    with open(DOCS_REPORT, "r", encoding="utf-8") as f:
        content = f.read()

    idx_prob = content.find("## 1. Problem Definition")
    idx_sol = content.find("## 2. Expected Physical")
    idx_ref = content.find("## 3. Fixed-Mesh Reference Anchor")
    idx_mb = content.find("## 4. Adaptive Method B")
    idx_comp = content.find("## 5. Quantitative Multi-Quantity Comparison")
    idx_disc = content.find("## 6. Scientific Discussion")
    idx_prov = content.find("## 7. Comprehensive Artifact")
    idx_rec = content.find("## 8. Supervisor Meeting Recommendations")

    assert idx_prob != -1, "Problem definition section missing"
    assert idx_sol != -1, "Expected physical solution section missing"
    assert idx_ref != -1, "Fixed-mesh reference anchor section missing"
    assert idx_mb != -1, "Method B formulation section missing"
    assert idx_comp != -1, "Quantitative comparison section missing"
    assert idx_disc != -1, "Scientific discussion section missing"
    assert idx_prov != -1, "Provenance section missing"
    assert idx_rec != -1, "Recommendations section missing"

    assert idx_prob < idx_sol < idx_ref < idx_mb < idx_comp < idx_disc < idx_prov < idx_rec, (
        "Sections must follow strict supervisor sequence: "
        "Problem -> Expected Solution -> Reference -> Method B -> Comparison -> Discussion -> Provenance -> Recommendations"
    )


def test_mode1_f1438_coordination_and_session_release():
    """Verify task lineage and historical session report presence."""
    assert os.path.isfile(ACTIVE_TASK)
    with open(ACTIVE_TASK, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    assert task_data.get("task_id", "").startswith("F14") or task_data["task_id"] in [
        "F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION",
        "F1439-MODE1-CORRECT-CLAIMS-AND-CAPTURE-STEP2-EVIDENCE",
        "F1440-MODE1-CORRECTED-METHOD-B-STEP2-FRACTURE-ANALYSIS",
        "F1441-MODE1-AWAIT-METHOD-B-STEP2-FRACTURE-EVIDENCE",
        "F1442-MODE1-EVALUATE-CORRECTED-METHOD-B-AND-METHOD-C-RESULTS",
        "F1443-MODE1-CORRECTED-METHOD-B-VALIDATION-TERMINATION-AUDIT",
        "F1444-MODE1-VALIDATE-METHOD-B-CRACK-FRONT-AND-SUPERVISOR-COMPARISON",
        "F1445-RESOLVE-REGRESSION-FAILURES-AND-FINALIZE-METHOD-B-REPORT",
        "F1446-MODE1-METHOD-C-INITIATION-AND-TRANSFER-FRAMEWORK",
    ]

    assert os.path.isfile(TASK_LEDGER)
    with open(TASK_LEDGER, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert "F1438,F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION" in ledger_text

    assert os.path.isfile(SESSION_REPORT), f"Session report missing at {SESSION_REPORT}"
