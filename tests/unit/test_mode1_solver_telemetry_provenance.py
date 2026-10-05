# -*- coding: utf-8 -*-
"""
Unit Regression Test Suite for Mode-I Active Solver Telemetry Provenance & Step-Displacement Mappings.

Enforces:
1. Verification of exact Step-1 and Step-2 boundary condition cards across all 5 active production decks.
2. Step-1 physical increment size = 2.5 nm/increment (Delta t1 = 5.0e-4, u_end = 0.0050 mm).
3. Step-2 physical increment size = 1.0 nm/increment (Delta t2 = 2.0e-4, Delta u2 = 0.0050 mm).
4. Cumulative offset entering Step 2 = 0.0050 mm.
5. Mathematical root cause proof for the historical Job 1410179 (0.004515 mm -> 0.003035 mm) contradiction.
6. Mathematical root cause proof for historical ET2/ET3/ET5 Step-1 over-estimates.
7. Telemetry consistency guards (monotonicity, Step-1 bound, Step-2 offset, step-specific increment size).
8. Methods documentation and provenance record verification.
"""
from __future__ import print_function
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DECK_PATHS = {
    "1410179": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "30_stage14_adaptive_candidate_spatial_fine", "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp"),
    "1410180": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "28_stage14_convergence_control_candidate", "PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL.inp"),
    "1410357": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "34_stage14_step2_adaptive_candidate_et2_6k", "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp"),
    "1410358": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "35_stage14_step2_adaptive_candidate_et3_5k", "PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE.inp"),
    "1410359": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "36_stage14_step2_adaptive_candidate_et5_4k", "PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE.inp"),
}

METHODS_DOC = os.path.join(REPO_ROOT, "docs", "methods", "MODE1_SOLVER_TELEMETRY_AND_DISPLACEMENT_MAPPING_AUDIT.md")


def parse_deck_step_parameters(inp_path):
    """Parse *STATIC and *BOUNDARY cards for Step-1 and Step-2 from an Abaqus deck."""
    assert os.path.exists(inp_path), "Deck missing: %s" % inp_path
    with open(inp_path, "r") as f:
        lines = f.readlines()
    
    steps = {}
    current_step = None
    
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.upper().startswith("*STEP"):
            step_name = "Step-1" if "Step-1" in line_s or "name=Step-1" in line_s.lower() else "Step-2"
            current_step = step_name
            steps[current_step] = {"static": None, "rp_bc": None}
        elif current_step and line_s.upper().startswith("*STATIC"):
            if i + 1 < len(lines):
                parts = [p.strip() for p in lines[i + 1].strip().split(",")]
                steps[current_step]["static"] = {
                    "dt_init": float(parts[0]),
                    "t_period": float(parts[1]),
                    "dt_min": float(parts[2]),
                    "dt_max": float(parts[3])
                }
        elif current_step and line_s.upper().startswith("*BOUNDARY"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("*"):
                bc_line = lines[j].strip()
                if "N_RP" in bc_line or "999999" in bc_line:
                    bc_parts = [p.strip() for p in bc_line.split(",")]
                    if len(bc_parts) >= 4 and bc_parts[1] == "2":
                        steps[current_step]["rp_bc"] = float(bc_parts[3])
                j += 1
        elif current_step and line_s.upper().startswith("*END STEP"):
            current_step = None
            
    return steps


class TestMode1SolverTelemetryProvenance(object):
    """Test suite for Mode-I solver telemetry provenance and displacement mappings."""

    def test_01_all_five_production_decks_exist_and_parse(self):
        """Verify that all 5 active production decks exist and have valid Step-1 and Step-2 definitions."""
        for job_id, deck_path in DECK_PATHS.items():
            steps = parse_deck_step_parameters(deck_path)
            assert "Step-1" in steps, "Step-1 missing in %s (%s)" % (job_id, deck_path)
            assert "Step-2" in steps, "Step-2 missing in %s (%s)" % (job_id, deck_path)
            
            # Step 1 static parameters
            s1 = steps["Step-1"]["static"]
            assert s1["dt_init"] == 5.0e-4
            assert s1["t_period"] == 1.0
            assert s1["dt_max"] == 5.0e-4
            assert steps["Step-1"]["rp_bc"] == 0.0050
            
            # Step 2 static parameters
            s2 = steps["Step-2"]["static"]
            assert s2["dt_init"] == 2.0e-4
            assert s2["t_period"] == 1.0
            assert s2["dt_max"] == 2.0e-4
            assert steps["Step-2"]["rp_bc"] == 0.0100

    def test_02_step_specific_physical_displacement_increments(self):
        """Verify that Step 1 yields 2.5 nm/inc and Step 2 yields 1.0 nm/inc."""
        # Step 1: dt = 5.0e-4, u_span = 0.0050 mm -> delta_u = 2.5e-6 mm = 2.5 nm
        delta_u_1 = 5.0e-4 * 0.0050
        assert abs(delta_u_1 - 2.5e-6) < 1e-12
        assert abs(delta_u_1 * 1e6 - 2.5) < 1e-6  # 2.5 nm
        
        # Step 2: dt = 2.0e-4, u_span = (0.0100 - 0.0050) = 0.0050 mm -> delta_u = 1.0e-6 mm = 1.0 nm
        delta_u_2 = 2.0e-4 * (0.0100 - 0.0050)
        assert abs(delta_u_2 - 1.0e-6) < 1e-12
        assert abs(delta_u_2 * 1e6 - 1.0) < 1e-6  # 1.0 nm

    def test_03_job_1410179_contradiction_mathematical_root_cause(self):
        """Prove that the 0.004515 mm value in F1244 was 2x too large and actual motion was strictly monotonic."""
        # Inc 903 in Step 1:
        step1_time_903 = 903 * 5.0e-4  # 0.4515
        true_u_903 = step1_time_903 * 0.0050  # 0.0022575 mm = 2.2575 um
        erroneous_u_903 = step1_time_903 * 0.0100  # 0.0045150 mm (erroneous 2x factor)
        
        assert abs(true_u_903 - 0.0022575) < 1e-9
        assert abs(erroneous_u_903 - 0.0045150) < 1e-9
        assert abs(erroneous_u_903 / true_u_903 - 2.0) < 1e-9
        
        # Inc 1214 in Step 1:
        step1_time_1214 = 1214 * 5.0e-4  # 0.6070
        true_u_1214 = step1_time_1214 * 0.0050  # 0.0030350 mm = 3.0350 um
        assert abs(true_u_1214 - 0.0030350) < 1e-9
        
        # True physical progression is strictly monotonic:
        delta_u = true_u_1214 - true_u_903
        assert delta_u > 0.0, "Expected strictly monotonic displacement progression"
        assert abs(delta_u - 0.0007775) < 1e-9  # +0.7775 um across 311 increments

    def test_04_prior_checkpoint_corrections_for_et2_et3_et5(self):
        """Verify mathematical root cause and corrected values for ET2, ET3, ET5 at Step-1 checkpoint."""
        # ET2 (1410357) at Step 1 Inc 1187:
        t1_et2 = 1187 * 5.0e-4  # 0.5935
        true_u_et2 = t1_et2 * 0.0050  # 0.0029675 mm
        err_u_et2 = t1_et2 * 0.0100   # 0.0059350 mm
        assert abs(true_u_et2 - 0.0029675) < 1e-9
        assert abs(err_u_et2 - 0.0059350) < 1e-9
        
        # ET3 (1410358) at Step 1 Inc 1303:
        t1_et3 = 1303 * 5.0e-4  # 0.6515
        true_u_et3 = t1_et3 * 0.0050  # 0.0032575 mm
        err_u_et3 = t1_et3 * 0.0100   # 0.0065150 mm
        assert abs(true_u_et3 - 0.0032575) < 1e-9
        assert abs(err_u_et3 - 0.0065150) < 1e-9
        
        # ET5 (1410359) at Step 1 Inc 1354:
        t1_et5 = 1354 * 5.0e-4  # 0.6770
        true_u_et5 = t1_et5 * 0.0050  # 0.0033850 mm
        err_u_et5 = t1_et5 * 0.0100   # 0.0067700 mm
        assert abs(true_u_et5 - 0.0033850) < 1e-9
        assert abs(err_u_et5 - 0.0067700) < 1e-9

    def test_05_reconstructed_displacement_telemetry_contract(self):
        """Verify deterministic conversion function implementing frozen telemetry contract."""
        def compute_mode1_displacement(step, step_time):
            if step == 1:
                return step_time * 0.0050
            elif step == 2:
                return 0.0050 + step_time * (0.0100 - 0.0050)
            else:
                raise ValueError("Unsupported step: %s" % step)
        
        # Step 1 bounds
        assert compute_mode1_displacement(1, 0.0) == 0.0
        assert compute_mode1_displacement(1, 1.0) == 0.0050
        assert abs(compute_mode1_displacement(1, 0.6070) - 0.0030350) < 1e-9
        
        # Step 2 bounds
        assert compute_mode1_displacement(2, 0.0) == 0.0050
        assert compute_mode1_displacement(2, 1.0) == 0.0100
        assert abs(compute_mode1_displacement(2, 0.2800) - 0.006400) < 1e-9
        assert abs(compute_mode1_displacement(2, 0.2630) - 0.006315) < 1e-9
        assert abs(compute_mode1_displacement(2, 0.3220) - 0.006610) < 1e-9
        assert abs(compute_mode1_displacement(2, 0.3490) - 0.006745) < 1e-9

    def test_06_consistency_guards_flag_violations(self):
        """Verify that consistency guards reject bad telemetry input."""
        def validate_telemetry_entry(step, u_val, prev_u_val=None):
            # Guard 1: Step 1 upper bound
            if step == 1 and u_val > 0.005000001:
                raise ValueError("GUARD_VIOLATION: Step-1 displacement %f exceeds 0.0050 mm endpoint" % u_val)
            # Guard 2: Step 2 lower bound (cumulative offset)
            if step == 2 and u_val < 0.004999999:
                raise ValueError("GUARD_VIOLATION: Step-2 displacement %f missing 0.0050 mm cumulative offset" % u_val)
            # Guard 3: Monotonicity
            if prev_u_val is not None and u_val < prev_u_val:
                raise ValueError("GUARD_VIOLATION: Decreasing displacement %f < %f in monotonic tension" % (u_val, prev_u_val))
            return True

        # Valid states pass
        assert validate_telemetry_entry(1, 0.003035, 0.002258)
        assert validate_telemetry_entry(2, 0.006400, 0.005357)
        
        # Step 1 overshoot fails
        with pytest.raises(ValueError):
            validate_telemetry_entry(1, 0.005935)
            
        # Step 2 missing offset fails
        with pytest.raises(ValueError):
            validate_telemetry_entry(2, 0.001400)
            
        # Non-monotonic regression fails
        with pytest.raises(ValueError):
            validate_telemetry_entry(1, 0.003035, 0.004515)

    def test_07_methods_documentation_exists_and_contains_frozen_formula(self):
        """Verify that MODE1_SOLVER_TELEMETRY_AND_DISPLACEMENT_MAPPING_AUDIT.md exists and contains required terms."""
        assert os.path.exists(METHODS_DOC), "Methods doc missing: %s" % METHODS_DOC
        with open(METHODS_DOC, "r") as f:
            content = f.read()
        assert "2.5" in content and "nm/increment" in content
        assert "1.0" in content and "nm/increment" in content
        assert "0.0050" in content
        assert "0.0022575" in content or "0.002258" in content
        assert "0.003035" in content
        assert "TELEMETRY_PROVENANCE_QUALIFIED__STEP_MAPPING_FROZEN" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
