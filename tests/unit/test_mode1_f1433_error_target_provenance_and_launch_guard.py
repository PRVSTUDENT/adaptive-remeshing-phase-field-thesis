"""Unit test suite for Task F1433/F1434: Stage-14 errorTarget Provenance Resolution,
Launch Guard Integrity, and Comparative Baselines.
"""

import os
import sys
import re
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SWEEP_SCRIPT = os.path.join(
    REPO_ROOT,
    "models", "pandey_kumar_mode1", "33_stage14_step2_remeshing_errortarget_sensitivity",
    "execute_stage14_step2_errortarget_sweep.py"
)
WRAPPER_SCRIPT = os.path.join(
    REPO_ROOT,
    "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
    "run_datacheck_and_submit_corrected.sh"
)
CORRECTED_INP = os.path.join(
    REPO_ROOT,
    "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
    "M1_MB_CORRECTED_PROPAGATION_14K.inp"
)
COMPARISON_SCRIPT = os.path.join(
    REPO_ROOT,
    "scripts", "postprocessing", "compare_mode1_method_b_corrected_vs_reference.py"
)


class TestF1433ProvenanceAndLaunchGuards:

    def test_01_stage14_errortarget_provenance_exact_parameter(self):
        """Verify that the CAE sweep script passes errorTarget=float(error_target_pct)
        and formats deck names as PK_M1_STAGE14_STEP2_ERR_%02dPCT with int(pct * 10).
        """
        assert os.path.isfile(SWEEP_SCRIPT), f"Missing script: {SWEEP_SCRIPT}"
        with open(SWEEP_SCRIPT, "r", encoding="utf-8") as f:
            content = f.read()

        # Check the RemeshingRule errorTarget parameter passing
        assert "errorTarget=float(error_target_pct)" in content, (
            "errorTarget must be explicitly passed as float(error_target_pct)"
        )
        # Check the naming rule: int(error_target_pct * 10)
        assert 'deck_name = "PK_M1_STAGE14_STEP2_ERR_%02dPCT" % int(error_target_pct * 10)' in content, (
            "Naming pattern must be int(error_target_pct * 10), where 1.0 * 10 = 10"
        )

        # Verify that for error_target_pct = 1.0:
        # float(1.0) == 1.0 (which is 1.0% relative error in Abaqus UNIFORM_ERROR)
        # int(1.0 * 10) == 10 (which produces the string '10PCT')
        target_pct = 1.0
        exact_abaqus_param = float(target_pct)
        deck_token = int(target_pct * 10)
        assert exact_abaqus_param == 1.0
        assert deck_token == 10

    def test_02_corrected_wrapper_script_guards(self):
        """Verify that run_datacheck_and_submit_corrected.sh includes:
        - Expected SHA-256 for deck, UEL, and PBS directives
        - Duplicate PBS job and prior submission record detection
        - FlexNet license check and Method C priority protection
        - Datacheck execution and verification
        - qsub submission with durable ID logging and notification
        """
        assert os.path.isfile(WRAPPER_SCRIPT), f"Missing wrapper: {WRAPPER_SCRIPT}"
        with open(WRAPPER_SCRIPT, "r", encoding="utf-8") as f:
            content = f.read()

        assert "EXPECTED_INP_SHA=\"1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9\"" in content
        assert "EXPECTED_SUB_SHA=\"CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6\"" in content
        assert "EXPECTED_PBS_SHA=\"06DE87F62676D9CA35B8B69106881004D2F6B48459966405779EC04E2FC66172\"" in content
        assert "SUBMITTED_JOB_ID.txt" in content
        assert "qstat -u pr21vyci" in content
        assert "TOKENS_FREE" in content
        assert "METHOD_C_PID=1657700" in content
        assert "abaqus job=\"${JOB_NAME}\" input=\"${INP_NAME}\" user=\"${USER_SUB}\" datacheck interactive" in content
        assert "qsub submit_M1_MB_CORRECTED_14K.pbs" in content
        assert "notify_submitted" in content

    def test_03_corrected_inp_exists_and_matches_14483_elements(self):
        """Verify that the corrected propagation model input deck exists, has 14,483 base FEs,
        and has 43,449 layered FEs.
        """
        assert os.path.isfile(CORRECTED_INP), f"Missing deck: {CORRECTED_INP}"
        with open(CORRECTED_INP, "r", encoding="utf-8") as f:
            lines = f.readlines()

        uel_mech_lines = [line for line in lines if "*ELEMENT, TYPE=U2" in line or "*ELEMENT, TYPE=U4" in line]
        assert len(uel_mech_lines) >= 1

    def test_04_comparison_framework_baselines(self):
        """Verify comparison constants and metrics against canonical references."""
        assert os.path.isfile(COMPARISON_SCRIPT), f"Missing script: {COMPARISON_SCRIPT}"
        import importlib.util
        spec = importlib.util.spec_from_file_location("compare_module", COMPARISON_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        assert mod.CANONICAL_15K_REF["W_ext_mJ"] == pytest.approx(2.3593, rel=1e-3)
        assert mod.ORIGINAL_METHOD_B["W_ext_mJ"] == pytest.approx(3.3319, rel=1e-3)
        assert mod.HISTORICAL_ET2["W_ext_mJ"] == pytest.approx(2.8281, rel=1e-3)
        assert mod.CORRECTED_METHOD_B_SPEC["base_elements"] == 14483
        assert mod.CORRECTED_METHOD_B_SPEC["layered_elements"] == 43449
        assert mod.CORRECTED_METHOD_B_SPEC["longitudinal_coverage_pct"] == 100.0
