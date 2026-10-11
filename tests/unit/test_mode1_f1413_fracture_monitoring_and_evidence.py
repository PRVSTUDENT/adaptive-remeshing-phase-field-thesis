"""
Unit test suite for Task F1413: Mode-I Fracture Monitoring, Reusable ODB Extraction,
and Matched Stiffness Parity Audit.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_extraction_and_harvest_scripts_exist():
    extractor = os.path.join(REPO_ROOT, "scripts", "postprocessing", "extract_mode1_fracture_odb.py")
    harvest_sh = os.path.join(REPO_ROOT, "scripts", "postprocessing", "harvest_mode1_terminal_results.sh")
    submit_pbs = os.path.join(REPO_ROOT, "scripts", "postprocessing", "submit_harvest_job.pbs")

    assert os.path.exists(extractor), "Extractor script must exist"
    assert os.path.exists(harvest_sh), "Harvest shell script must exist"
    assert os.path.exists(submit_pbs), "Submit PBS script must exist"

    # Verify SHA256 integrity
    assert compute_sha256(extractor) == "62A3352A98BA0C0073A7419443C85035B2E7A93854B71861D912B7BCE0CB37A5"
    assert compute_sha256(harvest_sh) == "CED641B6AF9E6E88017871951263579D30B168DC7467F9282730C6D7A2B7FD89"
    assert compute_sha256(submit_pbs) == "317BAF7EA0B8E7CD16948399BE28E09682506E47947B619C1785B5BF82161D03"

def test_matched_initial_stiffness_parity():
    native_json = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "m1_mb_native_14k_metrics.json")
    et2_json = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "m1_mb_et2_6k_metrics.json")

    assert os.path.exists(native_json), "Native metrics JSON must exist"
    assert os.path.exists(et2_json), "ET2 metrics JSON must exist"

    with open(native_json, "r") as f:
        m_nat = json.load(f)
    with open(et2_json, "r") as f:
        m_et2 = json.load(f)

    # 1. Native Method B matched K0 (u <= 0.0010 mm)
    k0_nat = m_nat["stiffness_u10"]["K0_kN_per_mm"]
    delta_k0_nat = m_nat["stiffness_u10"]["delta_vs_ref_pct"]
    r2_nat = m_nat["stiffness_u10"]["R2"]
    int_nat = m_nat["stiffness_u10"]["intercept_kN"]

    assert abs(delta_k0_nat) < 0.1, f"Native K0 error must be < 0.1%, got {delta_k0_nat}%"
    assert r2_nat > 0.99999, f"Native R2 must be > 0.99999, got {r2_nat}"
    assert abs(int_nat) < 1e-4, f"Native intercept must be < 1e-4 kN, got {int_nat}"
    assert m_nat["stiffness_u10"]["fit_points"] == 400

    # 2. Historical ET2 matched K0 (u <= 0.0010 mm)
    delta_k0_et2 = m_et2["stiffness_u10"]["delta_vs_ref_pct"]
    r2_et2 = m_et2["stiffness_u10"]["R2"]
    assert abs(delta_k0_et2) < 0.1, f"ET2 K0 error must be < 0.1%, got {delta_k0_et2}%"
    assert r2_et2 > 0.99999, f"ET2 R2 must be > 0.99999, got {r2_et2}"

def test_historical_et2_peak_load_and_softening_capture():
    et2_json = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "m1_mb_et2_6k_metrics.json")
    with open(et2_json, "r") as f:
        m_et2 = json.load(f)

    peak = m_et2["peak_reaction"]
    assert peak["is_captured"] is True, "Peak must be captured for ET2"
    assert 0.75 <= peak["F_max_kN"] <= 0.76, f"Peak force expected ~0.756 kN, got {peak['F_max_kN']}"
    assert 0.0058 <= peak["u_at_F_max_mm"] <= 0.0059, f"Peak displacement expected ~0.00584 mm, got {peak['u_at_F_max_mm']}"
    assert abs(peak["delta_F_max_pct"]) < 0.5, f"Peak force relative error must be < 0.5%, got {peak['delta_F_max_pct']}%"
    assert abs(peak["delta_u_peak_pct"]) < 0.5, f"Peak disp relative error must be < 0.5%, got {peak['delta_u_peak_pct']}%"

    # Terminal state must be in post-peak softening
    assert m_et2["terminal_u_mm"] > peak["u_at_F_max_mm"], "Terminal u must be greater than u(F_max)"
    assert m_et2["terminal_f_kN"] < 0.50, "Reaction force must have dropped significantly below peak"

def test_method_b_step1_steady_ramping():
    native_json = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "m1_mb_native_14k_metrics.json")
    with open(native_json, "r") as f:
        m_nat = json.load(f)

    # Must still be ramping pre-peak in Step 1
    assert m_nat["peak_reaction"]["is_captured"] is False, "Peak should not yet be captured in early Step 1"
    assert m_nat["terminal_u_mm"] > 0.0012, "Displacement must have advanced past 0.0012 mm"
    assert m_nat["terminal_f_kN"] > 0.18, "Reaction force must be > 0.18 kN"

def test_load_displacement_csv_integrity():
    csv_nat = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "m1_mb_native_14k_load_displacement.csv")
    csv_et2 = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "m1_mb_et2_6k_load_displacement.csv")

    assert os.path.exists(csv_nat), "Native CSV must exist"
    assert os.path.exists(csv_et2), "ET2 CSV must exist"

    with open(csv_nat, "r") as f:
        lines_nat = f.readlines()
    with open(csv_et2, "r") as f:
        lines_et2 = f.readlines()

    assert lines_nat[0].strip() == "step,inc_or_frame,u_mm,rf_raw_kN,f_kN,w_ext_mJ"
    assert lines_et2[0].strip() == "step,inc_or_frame,u_mm,rf_raw_kN,f_kN,w_ext_mJ"

    assert len(lines_nat) > 500, f"Expected >500 increments in native CSV, got {len(lines_nat)}"
    assert len(lines_et2) > 3000, f"Expected >3000 increments in ET2 CSV, got {len(lines_et2)}"

def test_decision_document_section13_presence():
    dec_doc = os.path.join(REPO_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")
    assert os.path.exists(dec_doc), "Decision document must exist"

    with open(dec_doc, "r", encoding="utf-8") as f:
        doc_text = f.read()

    assert "## 13. Task F1413 Closeout" in doc_text, "Section 13 must be present in decision doc"
    assert "F1413-METHOD-B-FRACTURE-MONITORING-AND-EVIDENCE-COLLECTION" in doc_text
    assert "Offline error-guided pre-refinement" in doc_text
    assert "137.891881" in doc_text
    assert "-0.0389" in doc_text
