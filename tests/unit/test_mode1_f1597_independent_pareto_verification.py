"""Unit tests for F1597 Independent Audit of Nonmatching State-Transfer Feasibility."""
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/reproduction_package_gate6b_energy/f42_mixed_uel.for"
EXPECTED_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CANDIDATE_DONOR_PATH = REPO_ROOT / "models/pandey_kumar_mode1/candidate_donor_h0025.inp"
EXPECTED_DONOR_SHA256 = "4C82B66BDA1D925C2BEA65CF765633897ACF4B0030E43C77647FA5E0D05A3179"
AUDIT_OUTPUT_PATH = REPO_ROOT / "results/validation/f1597_independent_pareto_verification_audit.json"


class TestMode1F1597IndependentParetoVerification(unittest.TestCase):
    """Test suite for independent Pareto verification and theorem audit."""

    def test_audit_execution_and_schema(self):
        """Verify that the independent audit script produces a valid schema 1 artifact."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.validation.audit_f1597_independent_pareto_verification import run_independent_audit

        data = run_independent_audit(REPO_ROOT)
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(data["status"], "PREPARATION_COMPLETE")
        self.assertTrue(data["verification_passed"])
        self.assertEqual(data["classification"], "NUMERICALLY_SUPPORTED_FOR_RESTRICTED_TRANSFER_FAMILY")

    def test_l2_projection_reduces_force_discrepancy(self):
        """Verify that L2 mass-matrix projection significantly reduces force error vs nodal interpolation."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.validation.audit_f1597_independent_pareto_verification import run_independent_audit

        data = run_independent_audit(REPO_ROOT)
        res = data["audit_data"]["variational_results"]
        interp_err = res["interpolation_baseline"]["rf2_error_pct"]
        l2_err = res["l2_projection"]["rf2_error_pct"]
        l2_gamma_err = res["l2_projection"]["fracture_energy_error_pct"]

        self.assertGreater(interp_err, 25.0, "Interpolation force error should be > 25%")
        self.assertLess(l2_err, 15.0, "L2 projection should reduce force error to < 15%")
        self.assertLessEqual(abs(l2_gamma_err), 2.0, "L2 fracture energy error should remain <= 2%")

    def test_simultaneous_continuity_demonstrated_for_frozen_damage(self):
        """Verify that a variational transfer operator achieves <= 5% force and <= 2% energy for frozen damage."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.validation.audit_f1597_independent_pareto_verification import run_independent_audit

        data = run_independent_audit(REPO_ROOT)
        res = data["audit_data"]["variational_results"]
        self.assertTrue(res["counterexample_found"], "Counterexample to universal impossibility should be found")

        ce = res["counterexample_details"]
        self.assertLessEqual(abs(ce["rf2_error_pct"]), 5.0, "Reaction force error must be <= 5%")
        self.assertLessEqual(abs(ce["fracture_energy_error_pct"]), 2.0, "Fracture energy error must be <= 2%")
        self.assertEqual(ce["healing_nodes"], 0, "Healing nodes must be 0")
        self.assertGreaterEqual(ce["damage_min"], 0.0, "Min damage must be >= 0")
        self.assertLessEqual(ce["damage_max"], 1.0, "Max damage must be <= 1")
        self.assertLessEqual(ce["mechanical_residual_kN"], 1e-10, "Mechanical residual must be <= 1e-10 kN")

    def test_crack_tip_surge_persistence_and_scaling_hypothesis(self):
        """Verify that crack-tip strain energy concentration surge persists across all fine-mesh transfer operators."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.validation.audit_f1597_independent_pareto_verification import run_independent_audit

        data = run_independent_audit(REPO_ROOT)
        res = data["audit_data"]["variational_results"]
        ce = res["counterexample_details"]

        # Surge ratio on 1 um mesh is > 12x
        self.assertGreater(ce["crack_tip_surge_ratio"], 12.0, "Crack-tip strain surge must be > 12x on fine mesh")
        
        # Verify classification distinction
        recon = data["audit_data"]["mathematical_reconstruction"]
        self.assertEqual(recon["strain_surge_in_unexecuted_donor_status"],
                         "Theoretical asymptotic scaling projection (psi0 ~ h^-1.58), not empirical measurement.")

    def test_production_uel_and_candidate_donor_hashes(self):
        """Verify bitwise integrity of production UEL and candidate donor input deck."""
        import hashlib
        def sha256(path):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while c := f.read(65536):
                    h.update(c)
            return h.hexdigest().upper()

        self.assertTrue(PRODUCTION_UEL_PATH.exists(), f"Missing production UEL: {PRODUCTION_UEL_PATH}")
        self.assertEqual(sha256(PRODUCTION_UEL_PATH), EXPECTED_UEL_SHA256)

        self.assertTrue(CANDIDATE_DONOR_PATH.exists(), f"Missing candidate donor deck: {CANDIDATE_DONOR_PATH}")
        self.assertEqual(sha256(CANDIDATE_DONOR_PATH), EXPECTED_DONOR_SHA256)


if __name__ == "__main__":
    unittest.main()
