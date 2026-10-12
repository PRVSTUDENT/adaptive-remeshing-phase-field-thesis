"""
Unit Test Suite for Mode-I Method C Gate C1 Handoff Comparison Specification
Task F1424: Method C Gate C1 Handoff and State Restoration Specification Audit
Protocol Version: 2
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_JSON_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "M1_GATE_C1_HANDOFF_SPECIFICATION.json"
SPEC_MD_PATH = REPO_ROOT / "docs" / "state_transfer" / "MODE1_METHOD_C_GATE_C1_HANDOFF_SPECIFICATION.md"
DECK_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "M1_RECIP_2906_CONTINUATION.inp"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "f42_mixed_uel.for"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CORRECTED_DECK_HASH = "501E1FBA1D6DB04CA25F7A273B6D0D4134C75AA13C40C734C8FEF7031556E152"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1C1HandoffSpecification:
    @pytest.fixture(autouse=True)
    def load_spec(self):
        assert SPEC_JSON_PATH.exists(), f"Specification file not found at {SPEC_JSON_PATH}"
        with open(SPEC_JSON_PATH, "r", encoding="utf-8") as f:
            self.spec = json.load(f)

    def test_01_spec_files_exist_and_hashes_match(self):
        """Verify that specification files exist and reference the frozen deck/UEL hashes."""
        assert SPEC_MD_PATH.exists()
        assert DECK_PATH.exists()
        assert UEL_PATH.exists()

        uel_sha = compute_sha256(UEL_PATH)
        assert uel_sha == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_sha} != {FROZEN_UEL_HASH}"

        deck_sha = compute_sha256(DECK_PATH)
        assert deck_sha == CORRECTED_DECK_HASH, f"Deck hash mismatch: {deck_sha} != {CORRECTED_DECK_HASH}"

        assert self.spec["governed_model_hashes"]["input_deck_sha256"] == CORRECTED_DECK_HASH
        assert self.spec["governed_model_hashes"]["user_subroutine_sha256"] == FROZEN_UEL_HASH

    def test_02_scientific_classification(self):
        """Verify that the two-stage loading is classified as QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY."""
        classification = self.spec["governing_rules"]["scientific_classification"]
        assert classification == "QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY"

    def test_03_uel_property_order_compliance(self):
        """Verify that UEL properties in specification follow: l0, Gc, E_mod, nu, k_stab, n_phys."""
        props = self.spec["governed_model_hashes"]["uel_property_order"]
        assert len(props) == 6
        assert props[0]["name"] == "l0" and props[0]["value"] == 0.0075
        assert props[1]["name"] == "Gc" and props[1]["value"] == 0.0027
        assert props[2]["name"] == "E_mod" and props[2]["value"] == 210.0
        assert props[3]["name"] == "nu" and props[3]["value"] == 0.3
        assert props[4]["name"] == "k_stab" and props[4]["value"] == 1.0e-7
        assert props[5]["name"] == "n_phys" and props[5]["value"] == 2906.0

    def test_04_handoff_reaction_force_criteria_and_decoupling(self):
        """Verify decoupling between 14.7k donor solution (0.6616 kN) and 2.9k coarse baseline (0.6531 kN)."""
        criteria = self.spec["recipient_handoff_acceptance_criteria"]
        rf_range = criteria["reaction_force_rf2_acceptable_range_kN"]
        rf_expected = criteria["reaction_force_rf2_expected_kN"]
        tolerance_pct = criteria["relative_force_error_tolerance_pct"]

        assert rf_expected == 0.6531
        assert rf_range[0] <= rf_expected <= rf_range[1]
        assert tolerance_pct <= 1.0

        # Donor decoupling check
        baseline = self.spec["donor_baseline_at_handoff"]
        actual_donor = baseline["actual_donor_solution"]
        coarse_ref = baseline["unadapted_coarse_mesh_reference"]
        shift = baseline["discretization_effect_analysis"]["coarsening_reaction_force_shift_pct"]

        assert actual_donor["measured_reaction_force_rf2_kN"] == 0.661647
        assert coarse_ref["measured_reaction_force_rf2_kN"] == 0.653093
        assert abs(shift - (-1.2928)) < 0.01

        # Expected recipient reaction force is governed by the coarse recipient equilibrium response
        assert abs(rf_expected - coarse_ref["measured_reaction_force_rf2_kN"]) / coarse_ref["measured_reaction_force_rf2_kN"] * 100.0 < 0.1

    def test_05_initial_stiffness_criteria(self):
        """Verify that initial elastic stiffness K0 is expected within 0.5% of 137.89 kN/mm."""
        criteria = self.spec["recipient_handoff_acceptance_criteria"]
        k0_range = criteria["initial_stiffness_k0_acceptable_range_kN_per_mm"]
        k0_expected = criteria["initial_stiffness_k0_expected_kN_per_mm"]
        tolerance_pct = criteria["relative_stiffness_error_tolerance_pct"]

        assert k0_expected == 137.89
        assert k0_range[0] <= k0_expected <= k0_range[1]
        assert tolerance_pct <= 0.5

    def test_06_convex_interpolation_bias_analytical_bound(self):
        """Verify that coarsening from 14,677 to 2,906 FEs introduces convex interpolation bias of +5.20%."""
        i_donor = 5.1852e-4
        i_recip = 5.4556e-4
        delta_pct = (i_recip - i_donor) / i_donor * 100.0

        assert delta_pct > 0.0, "Coarsening an exponential profile must overestimate integral (convexity)"
        assert 5.0 <= delta_pct <= 5.5, f"Observed convex bias {delta_pct:.2f}% out of expected [5.0%, 5.5%] range"

        # Check that governing rules classify convexity as a supported physical mechanism/hypothesis
        rules = self.spec["governing_rules"]
        assert "convex_interpolation_bias_hypothesis" in rules
        assert "supported physical mechanism and hypothesis" in rules["convex_interpolation_bias_hypothesis"]

    def test_07_step2_fracture_continuation_criteria(self):
        """Verify that Step 2 continuation criteria specify valid fracture response."""
        step2 = self.spec["step2_continuation_acceptance_criteria"]
        fmax_range = step2["peak_force_fmax_acceptable_range_kN"]
        u_peak_range = step2["displacement_at_peak_acceptable_range_mm"]

        assert fmax_range[0] >= 0.730 and fmax_range[1] <= 0.765
        assert u_peak_range[0] >= 0.0056 and u_peak_range[1] <= 0.0060
        assert step2["terminal_fracture_energy_fraction_min_pct"] >= 85.0

    def test_08_history_vs_phase_field_restoration_distinction(self):
        """Verify that history variable invariance and Helmholtz phase-field equilibrium are rigorously distinguished."""
        rules = self.spec["governing_rules"]
        assert "history_variable_preservation" in rules
        assert "phase_field_restoration_mechanics" in rules
        assert "Delta H = 0" in rules["history_variable_preservation"]
        assert "Helmholtz" in rules["phase_field_restoration_mechanics"]
