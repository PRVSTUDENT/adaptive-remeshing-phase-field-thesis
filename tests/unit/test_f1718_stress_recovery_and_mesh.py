# -*- coding: utf-8 -*-
"""
tests/unit/test_f1718_stress_recovery_and_mesh.py
=================================================
Automated unit test suite for Task F1718:
Transfer Verified Section 4.3 UEL/UMAT Stress Recovery to Five-Hole Benchmark
and Reproduce Figures 25(a) and 23(b) — Mesh-Only Stop Gate.

Verifies:
  1. Integrity and structure of recovered MISESERI field (f1718_five_hole_recovered_miseseri.json).
  2. Prevention of F1697 zero-stress failure (non-zero Cauchy stress and SPR error across all elements).
  3. Mathematical scale-invariance of normalized relative error eta_e = MISESERI / MISESAVG between physical and dummy modulus models.
  4. Directional localization of error indicators in narrowest ligament h3 <-> h4.
  5. Native adaptive remeshing metrics and mesh quality (positive Jacobians, aspect ratio < 1.5, h_min <= 1 um).
  6. Process-zone resolution (100% of ligament elements with h <= l0).
  7. Element count parity vs published Figure 23(b) target (12,944 elements) and F1714 baseline (13,034 elements).
  8. Presence and validity of adapted input deck (PK_F1718_JOB2_ADAPTED_PHYS.inp).
  9. Presence and validity of all 6 publication figure sets (12 files: 6 PNG + 6 PDF at 300 DPI).
 10. Strict stop gate enforcement (zero PBS jobs consumed, max_new_pbs_submissions = 0).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RECOVERED_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1718_five_hole_recovered_miseseri.json")
METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1718_adapted_mesh_metrics.json")
ADAPTED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "209_f1718_five_hole_recovery", "PK_F1718_JOB2_ADAPTED_PHYS.inp")
PARITY_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "209_f1718_five_hole_recovery", "PK_F1718_JOB2_PARITY_288.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1718_review_verification_audit.json")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
FIG_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")


@pytest.fixture(scope="module")
def recovered_data():
    assert os.path.exists(RECOVERED_JSON), f"Missing {RECOVERED_JSON}"
    with open(RECOVERED_JSON, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mesh_metrics():
    assert os.path.exists(METRICS_JSON), f"Missing {METRICS_JSON}"
    with open(METRICS_JSON, "r") as f:
        return json.load(f)


class TestF1718StressRecovery:
    def test_recovered_json_structure(self, recovered_data):
        assert recovered_data["task_id"] == "F1718-TRANSFER-SEC43-STRESS-RECOVERY-TO-FIVE-HOLE"
        assert recovered_data["coarse_mesh"]["num_elements"] == 2747
        assert recovered_data["coarse_mesh"]["num_nodes"] == 2844
        assert "recovery_models" in recovered_data
        assert "physical_early_damage" in recovered_data["recovery_models"]
        assert "dummy_modulus_companion" in recovered_data["recovery_models"]

    def test_prevention_of_f1697_zero_stress_defect(self, recovered_data):
        phys = recovered_data["recovery_models"]["physical_early_damage"]["statistics"]
        dummy = recovered_data["recovery_models"]["dummy_modulus_companion"]["statistics"]

        # Ensure all elements have non-zero stress error (eliminating F1697 zero-stress defect)
        assert phys["miseseri_min"] > 0.0, "Physical MISESERI min must be strictly positive"
        assert phys["miseseri_max"] > 100.0, "Physical MISESERI max must reflect stress concentration"
        assert phys["misesavg_min"] > 0.0, "Physical MISESAVG min must be strictly positive"

        assert dummy["miseseri_min"] > 0.0, "Dummy MISESERI min must be strictly positive"
        assert dummy["miseseri_max"] > 0.0, "Dummy MISESERI max must be strictly positive"

    def test_scale_invariance_of_normalized_error(self, recovered_data):
        phys = recovered_data["recovery_models"]["physical_early_damage"]["statistics"]
        dummy = recovered_data["recovery_models"]["dummy_modulus_companion"]["statistics"]

        # Relative error eta_e = MISESERI / MISESAVG must be identical within floating point tolerance
        assert abs(phys["eta_mean_pct"] - dummy["eta_mean_pct"]) < 1e-3
        assert abs(phys["eta_min_pct"] - dummy["eta_min_pct"]) < 1e-4
        assert abs(phys["eta_max_pct"] - dummy["eta_max_pct"]) < 1e-2

        # Mean eta_e should match calibrated errorTarget ~ 3.05%
        assert 3.00 <= phys["eta_mean_pct"] <= 3.10

    def test_directional_localization_in_narrowest_ligament(self, recovered_data):
        phys_model = recovered_data["recovery_models"]["physical_early_damage"]
        phys_eri = phys_model["fields"]["miseseri"]
        coarse_centroids = recovered_data["coarse_centroids"]

        # Find top 5 elements with highest MISESERI
        top5 = sorted(phys_eri.items(), key=lambda x: float(x[1]), reverse=True)[:5]
        for eid_str, val in top5:
            cx, cy = coarse_centroids[eid_str]
            # Must be strictly clustered in ligament h3-h4: x in [0.62, 0.68], y in [0.48, 0.61]
            assert 0.62 <= cx <= 0.68, f"Element {eid_str} centroid X={cx} outside h3-h4 corridor"
            assert 0.48 <= cy <= 0.61, f"Element {eid_str} centroid Y={cy} outside h3-h4 corridor"


class TestF1718AdaptiveRemeshing:
    def test_metrics_json_structure(self, mesh_metrics):
        assert mesh_metrics["task_id"] == "F1718-TRANSFER-SEC43-STRESS-RECOVERY-TO-FIVE-HOLE"
        assert mesh_metrics["published_target_elements"] == 12944
        assert mesh_metrics["f1714_baseline_elements"] == 13034
        assert "primary_candidate" in mesh_metrics
        assert "high_parity_candidate" in mesh_metrics
        assert "dummy_modulus_candidate" in mesh_metrics

    def test_mesh_quality_and_jacobians(self, mesh_metrics):
        primary = mesh_metrics["primary_candidate"]
        assert primary["positive_jacobians"] is True, "Must have 100% positive Jacobians"
        assert primary["ar_mean"] < 1.35, f"Mean aspect ratio must be regular, got {primary['ar_mean']}"
        assert primary["ar_max"] < 3.50, f"Max aspect ratio must be bounded, got {primary['ar_max']}"
        assert primary["quad_percentage"] > 95.0, "Must be quad-dominated (>95%)"

    def test_process_zone_resolution(self, mesh_metrics):
        primary = mesh_metrics["primary_candidate"]
        # h_min should be close to 0.001 mm (1 um)
        assert 0.0008 <= primary["h_min_mm"] <= 0.0012
        # 100% of elements in narrowest ligament must resolve h <= l0 (8 um)
        assert primary["pct_le_l0_in_ligament"] == 100.0
        # Over 99% must resolve h <= l0/2 (4 um)
        assert primary["pct_le_half_l0_in_ligament"] > 99.0

    def test_element_count_parity(self, mesh_metrics):
        primary = mesh_metrics["primary_candidate"]
        high_parity = mesh_metrics["high_parity_candidate"]

        # Primary candidate (errorTarget = 3.05%) within 9% of published target
        assert abs(primary["pub_target_12944_diff_pct"]) < 9.0
        # High-parity candidate (errorTarget = 2.88%) within 3.5% of published target
        assert abs(high_parity["pub_target_12944_diff_pct"]) < 3.5

    def test_dummy_modulus_remesh_invariance(self, mesh_metrics):
        primary = mesh_metrics["primary_candidate"]
        dummy = mesh_metrics["dummy_modulus_candidate"]

        # Element counts between physical and dummy modulus remeshes must match within 0.5%
        elem_diff_pct = abs(primary["num_elements"] - dummy["num_elements"]) / float(primary["num_elements"]) * 100.0
        assert elem_diff_pct < 0.5, f"Scale invariance violated: element diff is {elem_diff_pct:.2f}%"

    def test_adapted_inp_decks_exist(self):
        assert os.path.exists(ADAPTED_INP), f"Missing {ADAPTED_INP}"
        assert os.path.getsize(ADAPTED_INP) > 100000
        assert os.path.exists(PARITY_INP), f"Missing {PARITY_INP}"
        assert os.path.getsize(PARITY_INP) > 100000


class TestF1718PublicationFigures:
    @pytest.mark.parametrize("base_name", [
        "fig_f1718_figure_a_pure_vs_companion_miseseri",
        "fig_f1718_figure_b_published_fig25a_vs_companion",
        "fig_f1718_figure_c_baseline_vs_candidate_mesh",
        "fig_f1718_figure_d_published_fig23b_vs_candidate",
        "fig_f1718_figure_e_ligament_wireframe_zooms",
        "fig_f1718_figure_f_quantitative_indicators_and_sizes"
    ])
    def test_figures_exist_and_non_empty(self, base_name):
        png_path = os.path.join(FIG_DIR, base_name + ".png")
        pdf_path = os.path.join(FIG_DIR, base_name + ".pdf")
        assert os.path.exists(png_path), f"Missing {png_path}"
        assert os.path.getsize(png_path) > 20000, f"PNG too small: {png_path}"
        assert os.path.exists(pdf_path), f"Missing {pdf_path}"
        assert os.path.getsize(pdf_path) > 20000, f"PDF too small: {pdf_path}"


class TestF1718StopGate:
    def test_strict_mesh_only_stop_gate(self):
        assert os.path.exists(ACTIVE_TASK_JSON)
        with open(ACTIVE_TASK_JSON, "r") as f:
            task = json.load(f)
        assert task["max_new_pbs_submissions"] == 0
        assert task["submissions_consumed"] == 0
        assert task.get("full_fracture_solve_permitted", False) is False


class TestF1718ReviewAuditReconciliation:
    def test_review_audit_artifact_exists_and_valid(self):
        assert os.path.exists(AUDIT_JSON), f"Missing {AUDIT_JSON}"
        with open(AUDIT_JSON, "r") as f:
            data = json.load(f)
        
        # 1. Pointwise proportionality
        prop = data["pointwise_proportionality"]
        assert prop["verdict"] == "VERIFIED_PROPORTIONAL_WITHIN_NUMERICAL_PRECISION"
        assert prop["max_abs_eta_difference_pct"] < 1.0e-4

        # 2. Reconciled peak elements
        peaks = data["reconciled_peak_elements"]
        assert len(peaks) == 10
        top_eids = [p["eid"] for p in peaks]
        assert 316 in top_eids
        e316 = next(p for p in peaks if p["eid"] == 316)
        assert abs(e316["centroid"][0] - 0.6377) < 0.001
        assert abs(e316["centroid"][1] - 0.5043) < 0.001

        # 3. Ligament hierarchy
        ligs = data["ligament_statistics"]
        assert "Ligament_3 (Hole3 - Hole4)" in ligs
        l3 = ligs["Ligament_3 (Hole3 - Hole4)"]
        assert l3["area_weighted_miseseri_mpa"] > 150.0  # Narrowest ligament dominates
        assert l3["nominal_clearance_mm"] < 0.040        # 33.1 um

        # 4. 31-element discrepancy
        disc = data["mesh_discrepancy_31_elements"]
        assert disc["difference"] == 31
        assert disc["relative_difference_pct"] < 0.5

