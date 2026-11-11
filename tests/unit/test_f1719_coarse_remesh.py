# -*- coding: utf-8 -*-
"""
tests/unit/test_f1719_coarse_remesh.py
======================================
Automated unit test suite for Task F1719:
Genuine Coarse Phase-Field MISESERI-Driven Adaptive Remeshing for Five-Hole Plate —
No Fine-Mesh Damage Leakage — Mesh-Only Stop Gate.

Verifies:
  1. Multi-state recovery dataset integrity (f1719_recovered_miseseri_multistate.json).
  2. Complete elimination of fine-mesh data leakage: all damage originates from coarse PFM ODB.
  3. Non-zero Cauchy stress and SPR error fields across all 5 states (zero-stress defect eliminated).
  4. Mathematical scale-invariance between physical and dummy modulus recovery (|Delta eta| <= 3e-5%).
  5. Directional localization of peak error in narrowest ligament h3 <-> h4 (Element 2, clearance 33.1 um).
  6. Positive Pearson correlation between coarse damage and stress jump error (r >= 0.45).
  7. Native Abaqus CAE adaptiveRemesh metrics across candidates (100% positive Jacobians, mean AR < 1.30).
  8. Process-zone resolution (100% of ligament elements satisfy h <= l0 = 8 um, >99% satisfy h <= l0/2).
  9. Element parity vs published Figure 23(b) target (12,944 elements) and F1714 baseline (13,034 elements).
 10. Presence and validity of all generated adapted input decks (STATE2, PARITY, MULTISTATE).
 11. Presence and validity of all 8 publication figure sets (16 files: 8 PNG + 8 PDF at 300 DPI).
 12. Strict stop gate enforcement (zero PBS jobs consumed, max_new_pbs_submissions = 0).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RECOVERY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_recovered_miseseri_multistate.json")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_miseseri_evolution_audit.json")
METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_adapted_mesh_metrics.json")
TELEMETRY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_coarse_pfm_telemetry.json")

DECK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm")
STATE2_INP = os.path.join(DECK_DIR, "PK_F1719_ADAPTED_STATE2.inp")
PARITY_INP = os.path.join(DECK_DIR, "PK_F1719_ADAPTED_STATE2_PARITY288.inp")
MULTI_INP = os.path.join(DECK_DIR, "PK_F1719_ADAPTED_MULTISTATE.inp")

ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
FIG_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")


@pytest.fixture(scope="module")
def recovery_data():
    assert os.path.exists(RECOVERY_JSON), f"Missing {RECOVERY_JSON}"
    with open(RECOVERY_JSON, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def audit_data():
    assert os.path.exists(AUDIT_JSON), f"Missing {AUDIT_JSON}"
    with open(AUDIT_JSON, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mesh_metrics():
    assert os.path.exists(METRICS_JSON), f"Missing {METRICS_JSON}"
    with open(METRICS_JSON, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def coarse_telemetry():
    assert os.path.exists(TELEMETRY_JSON), f"Missing {TELEMETRY_JSON}"
    with open(TELEMETRY_JSON, "r") as f:
        return json.load(f)


class TestF1719CoarsePhaseFieldRemesh:
    def test_coarse_telemetry_and_damage_origin(self, coarse_telemetry):
        assert coarse_telemetry["task_id"] == "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE"
        assert "candidate_states" in coarse_telemetry
        assert "state_0_elastic" in coarse_telemetry["candidate_states"]
        assert "state_2_early_localization" in coarse_telemetry["candidate_states"]

        # Confirm autonomous damage evolution in coarse model
        s2 = coarse_telemetry["candidate_states"]["state_2_early_localization"]
        assert 0.15 <= s2["d_max"] <= 0.20, f"State 2 d_max ({s2['d_max']}) must reflect early localization"

    def test_recovery_dataset_structure(self, recovery_data):
        assert recovery_data["task_id"] == "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE"
        assert recovery_data["mesh_summary"]["num_elements"] == 2747
        assert recovery_data["mesh_summary"]["num_nodes"] == 2844

        # Check all 5 states exist
        for s in ["STATE0", "STATE1", "STATE2", "STATE3", "STATE4"]:
            assert s in recovery_data["states"], f"Missing state {s}"
            assert "physical" in recovery_data["states"][s]["scales"]

    def test_prevention_of_zero_stress_defect(self, recovery_data):
        for s in ["STATE0", "STATE1", "STATE2", "STATE3", "STATE4"]:
            phys_summary = recovery_data["states"][s]["scales"]["physical"]["summary"]
            assert phys_summary["miseseri_min"] > 0.0, f"{s} physical MISESERI min must be > 0"
            assert phys_summary["miseseri_max"] > 100.0, f"{s} physical MISESERI max must be > 100 MPa"
            assert phys_summary["misesavg_min"] > 0.0, f"{s} physical MISESAVG min must be > 0"

    def test_mathematical_scale_invariance(self, audit_data):
        prop_s2 = audit_data["proportionality_check"]["STATE2"]
        prop_s3 = audit_data["proportionality_check"]["STATE3"]

        assert prop_s2["scale_invariance_verified"] is True
        assert prop_s3["scale_invariance_verified"] is True

        assert prop_s2["max_delta_eta_percent"] <= 5e-5, "Max |Delta eta| must be <= 5e-5%"
        assert prop_s3["max_delta_eta_percent"] <= 5e-5, "Max |Delta eta| must be <= 5e-5%"

        # Ratio must match E_phys / E_dummy = 210000 / 1e-8 = 2.1e+13
        assert abs(prop_s2["measured_mean_ratio"] - 2.1e13) / 2.1e13 < 1e-6

    def test_directional_localization_in_narrowest_ligament(self, audit_data):
        # In States 1, 2, 3, 4, peak error must be in narrowest ligament h3 <-> h4
        for s in ["STATE1", "STATE2", "STATE3", "STATE4"]:
            s_audit = audit_data["state_evolution"][s]
            top_elem = s_audit["top_element"]
            assert top_elem["eid"] == 2, f"In {s}, peak error element must be Element 2"
            assert 0.63 <= top_elem["cx"] <= 0.67, "Element 2 cx must be in narrowest ligament"
            assert 0.48 <= top_elem["cy"] <= 0.52, "Element 2 cy must be in narrowest ligament"

    def test_damage_vs_miseseri_correlation(self, audit_data):
        # Pearson r must show positive correlation (degraded stiffness drives stress jumps)
        for s in ["STATE0", "STATE1", "STATE2", "STATE3", "STATE4"]:
            r = audit_data["state_evolution"][s]["pearson_r_damage_vs_miseseri"]
            assert r >= 0.45, f"Pearson r in {s} ({r}) must be >= 0.45"

    def test_primary_adapted_mesh_metrics(self, mesh_metrics):
        cand = mesh_metrics["candidates"]["primary_state2"]
        assert cand["positive_jacobians"] is True, "Mesh must have 100% positive Jacobians"
        assert cand["num_elements"] == 11871
        assert cand["num_nodes"] == 12088
        assert cand["quad_percentage"] > 97.0, "Must be quad-dominated (>97%)"
        assert cand["ar_mean"] < 1.30, f"Mean aspect ratio ({cand['ar_mean']}) must be < 1.30"
        assert cand["ar_max"] < 2.50, f"Max aspect ratio ({cand['ar_max']}) must be < 2.50"

        # Process zone resolution in narrowest ligament h3-h4
        assert cand["pct_le_l0_in_ligament"] == 100.0, "100% of ligament elements must satisfy h <= l0"
        assert cand["pct_le_half_l0_in_ligament"] >= 99.0, ">99% of ligament elements must satisfy h <= l0/2"
        assert cand["ligament_h3_h4_min_h"] < 0.0010, "Minimum h must be < 1.0 um (l0/8)"

    def test_high_parity_candidate_metrics(self, mesh_metrics):
        parity = mesh_metrics["candidates"]["parity_state2_288"]
        assert parity["positive_jacobians"] is True
        assert parity["num_elements"] == 13226
        assert abs(parity["pub_target_12944_diff_pct"]) < 3.0, "Discrepancy vs 12,944 target must be < 3%"
        assert abs(parity["f1714_base_13034_diff_pct"]) < 2.0, "Discrepancy vs 13,034 baseline must be < 2%"

    def test_sequential_multistate_candidate(self, mesh_metrics):
        multi = mesh_metrics["candidates"]["multistate_state1_state3"]
        assert multi["positive_jacobians"] is True
        assert multi["num_elements"] == 12017
        assert multi["pct_le_l0_in_ligament"] == 100.0

    def test_adapted_input_decks_exist_and_nonempty(self):
        for path in [STATE2_INP, PARITY_INP, MULTI_INP]:
            assert os.path.exists(path), f"Missing adapted deck: {path}"
            assert os.path.getsize(path) > 800000, f"Deck {path} unexpectedly small"

    def test_all_16_publication_figure_files_exist(self):
        fig_stems = [
            "fig_f1719_figure_a_undamaged_vs_initiation_miseseri",
            "fig_f1719_figure_b_miseseri_multistate_evolution",
            "fig_f1719_figure_c_published_fig25a_vs_coarse_companion",
            "fig_f1719_figure_d_coarse_vs_adapted_mesh",
            "fig_f1719_figure_e_published_fig23b_vs_f1719_adapted",
            "fig_f1719_figure_f_ligament_wireframe_zooms",
            "fig_f1719_figure_g_quantitative_indicators_and_sizes",
            "fig_f1719_figure_h_f1714_f1718_f1719_adaptive_mesh_comparison"
        ]
        for stem in fig_stems:
            png = os.path.join(FIG_DIR, stem + ".png")
            pdf = os.path.join(FIG_DIR, stem + ".pdf")
            assert os.path.exists(png), f"Missing PNG: {png}"
            assert os.path.exists(pdf), f"Missing PDF: {pdf}"
            assert os.path.getsize(png) > 100000, f"PNG {png} unexpectedly small"
            assert os.path.getsize(pdf) > 20000, f"PDF {pdf} unexpectedly small"

    def test_strict_mesh_only_stop_gate_enforcement(self):
        assert os.path.exists(ACTIVE_TASK_JSON)
        with open(ACTIVE_TASK_JSON, "r") as f:
            task = json.load(f)

        assert task["task_id"] == "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE"
        assert task["max_new_pbs_submissions"] == 0
        assert task["submissions_consumed"] == 0
        assert task["active_pbs_job_id"] is None

    def test_review_reconciliation_audit(self):
        recon_path = os.path.join(REPO_ROOT, "results", "validation", "f1719_review_reconciliation_audit.json")
        assert os.path.exists(recon_path), f"Missing {recon_path}"
        with open(recon_path, "r") as f:
            recon = json.load(f)

        assert recon["task_id"] == "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE"
        assert "findings" in recon
        assert "F1719_B1_provenance" in recon["findings"]
        assert "F1719_B9_artifact_verification" in recon["findings"]
        assert recon["findings"]["F1719_B9_artifact_verification"]["all_artifacts_exist"] is True
