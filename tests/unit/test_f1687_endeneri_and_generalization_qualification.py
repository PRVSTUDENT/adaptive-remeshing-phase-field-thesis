"""
tests/unit/test_f1687_endeneri_and_generalization_qualification.py
==================================================================
Task F1687 Unit and Regression Test Suite:
1. Frozen UEL SHA-256 invariance verification.
2. Stage B: Terminal ENDENERI control audit (H1 falsification).
3. Stage C: Mode-I blind differential generalization audit (H2 falsification under adopted thresholds).
4. Stage D: Thesis figures existence and report build verification.
5. Zero new PBS jobs policy enforcement.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_f1687_frozen_uel_invariance():
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), "Frozen UEL source must exist"
    actual_sha = compute_sha256(uel_path)
    assert actual_sha == FROZEN_UEL_SHA256, "Frozen UEL must remain strictly unmodified"

def test_f1687_endeneri_terminal_control_audit():
    inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "candidates", "PK_HOLE_ENDENERI_TERM_PHYS.inp")
    assert os.path.exists(inp_path), "ENDENERI terminal control candidate deck must exist"

    audit_path = os.path.join(REPO_ROOT, "results", "validation", "f1687_endeneri_candidate_audit.json")
    assert os.path.exists(audit_path), "ENDENERI candidate audit JSON must exist"
    with open(audit_path, "r") as fp:
        audit = json.load(fp)

    assert audit["total_elements"] == 51712, "Physical elements must match 51,712"
    assert audit["w90_um"] > 150.0, "W90 must exceed 150 um (severe width inflation)"
    assert audit["waste_pct_rel"] > 85.0, "Waste must exceed 85% (fails Criterion 3)"
    assert audit["h1_hypothesis_verdict"] == "FALSIFIED", "Hypothesis H1 must be decisively falsified"

def test_f1687_mode1_blind_generalization_audit():
    inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "01_standard_pfm_reference", "PK_MODE1_BLIND_DIFF_PHYS.inp")
    assert os.path.exists(inp_path), "Mode-I blind generalization candidate deck must exist"

    audit_path = os.path.join(REPO_ROOT, "results", "validation", "f1687_mode1_blind_audit.json")
    assert os.path.exists(audit_path), "Mode-I blind candidate audit JSON must exist"
    with open(audit_path, "r") as fp:
        audit = json.load(fp)

    assert audit["n_elements"] == 11578, "Mode-I adapted physical elements must match 11,578"
    assert audit["crack_corridor"]["median_h_equiv_um"] <= 2.50, "Corridor median h_equiv must satisfy <= l0/3 = 2.50 um"
    assert audit["transverse_width"]["w50_um"] <= 20.0, "Core ligament width W50 must be narrow (<= 20 um)"
    assert audit["transverse_width"]["w90_um"] > 50.0, "W90 must exceed 50.0 um due to terminal boundary stress flare"
    assert audit["selectivity_and_waste"]["relative_waste_pct"] > 70.0, "Relative waste must exceed 70.0% (fails Criterion 3)"
    assert audit["hypothesis_h2_verdict"] == "FALSIFIED", "Hypothesis H2 must be falsified under adopted thresholds"

def test_f1687_thesis_figures_and_pdf():
    fig1 = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1687_endeneri_comparison.pdf")
    fig2 = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1687_synthesis_and_generalization.pdf")
    assert os.path.exists(fig1), "Figure 5.17 must exist"
    assert os.path.exists(fig2), "Figure 5.18 must exist"

    pdf_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "main.pdf")
    assert os.path.exists(pdf_path), "main.pdf must exist"
    assert os.path.getsize(pdf_path) > 50000000, "main.pdf size must be valid (> 50 MB)"

def test_f1687_zero_new_pbs_submissions_policy():
    active_task = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task, "r") as fp:
        task = json.load(fp)
    assert task["max_new_pbs_submissions"] == 0, "max_new_pbs_submissions must strictly equal 0"
