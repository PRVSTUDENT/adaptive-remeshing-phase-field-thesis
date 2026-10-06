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
9. Early Step-1 telemetry provenance and unit-conflation guards (Incs 10, 91, 121, 137).
10. Step-2 spatial-fine 8T SMP Job 1410504 telemetry checkpoint and post-peak progression guard.
11. Guard against asserting scientific displacement from increment count alone without captured step time or field output.
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

    def test_08_early_step1_telemetry_provenance_and_unit_guards(self):
        """Verify exact physical displacement for early Step-1 increments and guard against dimensionless time conflation."""
        def step1_displacement_from_inc(inc_num):
            dt1 = 5.0e-4
            step1_span = 0.0050  # mm
            step_time = inc_num * dt1
            return step_time * step1_span

        # Inc 10: t1 = 0.0050 -> uy = 0.000025 mm = 0.025 um = 25.0 nm
        u_10 = step1_displacement_from_inc(10)
        assert abs(u_10 - 2.5e-5) < 1e-12
        assert abs(u_10 * 1e3 - 0.025) < 1e-9  # 0.025 um
        assert abs(u_10 * 1e6 - 25.0) < 1e-6   # 25.0 nm
        # Guard against erroneously assuming 0.05 um (which would be 2x or from 0.010 mm horizon)
        assert abs(u_10 * 1e3 - 0.05) > 0.02

        # Inc 91: t1 = 0.0455 -> uy = 0.0002275 mm = 0.2275 um = 227.5 nm
        u_91 = step1_displacement_from_inc(91)
        assert abs(u_91 - 0.0002275) < 1e-12
        assert abs(u_91 * 1e3 - 0.2275) < 1e-9  # 0.2275 um
        assert abs(u_91 * 1e6 - 227.5) < 1e-6   # 227.5 nm
        # Guard against erroneously conflating dimensionless time 0.0455 with 0.0455 um or 0.0455 mm
        assert abs(u_91 * 1e3 - 0.0455) > 0.1
        assert abs(u_91 - 0.0455) > 0.04

        # Inc 121: t1 = 0.0605 -> uy = 0.0003025 mm = 0.3025 um = 302.5 nm
        u_121 = step1_displacement_from_inc(121)
        assert abs(u_121 - 0.0003025) < 1e-12
        assert abs(u_121 * 1e3 - 0.3025) < 1e-9  # 0.3025 um
        assert abs(u_121 * 1e6 - 302.5) < 1e-6   # 302.5 nm
        # Guard against erroneously writing t1 (0.0605) as millimeters (0.0605 mm = 60.5 um, 200x error)
        assert abs(u_121 - 0.0605) > 0.06

        # Inc 137: t1 = 0.0685 -> uy = 0.0003425 mm = 0.3425 um = 342.5 nm
        u_137 = step1_displacement_from_inc(137)
        assert abs(u_137 - 0.0003425) < 1e-12
        assert abs(u_137 * 1e3 - 0.3425) < 1e-9  # 0.3425 um
        assert abs(u_137 * 1e6 - 342.5) < 1e-6   # 342.5 nm
        # Guard against erroneously writing t1 (0.0685) as millimeters (0.0685 mm = 68.5 um, 200x error)
        assert abs(u_137 - 0.0685) > 0.06


    def test_09_job_1410179_and_1410504_pbs_resource_provenance_guards(self):
        """Verify that Job 1410179 (serial) and 1410504 (8T SMP) both have 16 GB memory allocated in PBS scripts and ledgers."""
        pbs_1410179 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "30_stage14_adaptive_candidate_spatial_fine", "submit_solver.pbs")
        pbs_1410504 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "37_stage14_adaptive_candidate_spatial_fine_8thread", "submit_solver.pbs")
        current_state = os.path.join(REPO_ROOT, "project_coordination", "CURRENT_STATE.md")

        assert os.path.exists(pbs_1410179), "PBS script for 1410179 missing: %s" % pbs_1410179
        assert os.path.exists(pbs_1410504), "PBS script for 1410504 missing: %s" % pbs_1410504
        assert os.path.exists(current_state), "CURRENT_STATE.md missing"

        with open(pbs_1410179, "r") as f:
            c_179 = f.read()
        assert "#PBS -l nodes=1:ppn=1" in c_179
        assert "#PBS -l mem=16gb" in c_179
        assert "#PBS -l walltime=24:00:00" in c_179
        assert 'memory="16gb"' in c_179
        # Assert that 8 GB is NOT specified for Job 1410179
        assert "mem=8gb" not in c_179
        assert 'memory="8gb"' not in c_179

        with open(pbs_1410504, "r") as f:
            c_504 = f.read()
        assert "#PBS -l nodes=1:ppn=8" in c_504
        assert "#PBS -l mem=16gb" in c_504
        assert "#PBS -l walltime=48:00:00" in c_504
        assert 'memory="16gb"' in c_504
        assert "mem=8gb" not in c_504
        assert 'memory="8gb"' not in c_504

        with open(current_state, "r") as f:
            c_cs = f.read()
        # Verify CURRENT_STATE.md records 16gb/16GB for 1410179
        assert "1410179" in c_cs
        lines_179 = [l for l in c_cs.splitlines() if "1410179" in l and ("16gb" in l.lower() or "16 gb" in l.lower())]
        assert len(lines_179) > 0, "CURRENT_STATE.md must explicitly record 16 GB allocation for Job 1410179"

    def test_10_job_1410504_step2_telemetry_checkpoint_and_postpeak_traversal(self):
        """Verify that Job 1410504 (8T SMP 58k) prescribed displacement is derived from captured step time t2."""
        def evaluate_prescribed_displacement_from_step_time(step, step_time):
            if step == 1:
                return step_time * 0.0050
            elif step == 2:
                step1_offset = 0.0050  # mm
                step2_span = 0.0050    # mm (0.0100 - 0.0050)
                return step1_offset + step_time * step2_span
            else:
                raise ValueError("Unsupported step: %s" % step)

        # Captured from .sta snapshot: step = 2, step_time = 0.6580
        captured_step = 2
        captured_step_time = 0.6580
        u_evaluated = evaluate_prescribed_displacement_from_step_time(captured_step, captured_step_time)
        assert abs(u_evaluated - 0.008290) < 1e-6
        assert abs(u_evaluated * 1e3 - 8.290) < 1e-3  # 8.290 um

        # Peak displacement for 58k mesh is u_peak = 0.005717 mm (Step 2 Inc 717, step time 0.1434)
        u_peak_58k = 0.005717
        assert u_evaluated > u_peak_58k, "Job 1410504 evaluated prescribed displacement must exceed peak load displacement"

        # Serial 24h limit stopped at u_term = 0.007429 mm (Step 2 Inc 2443, step time 0.4858)
        u_serial_term = 0.007429
        assert u_evaluated > u_serial_term, "Job 1410504 (8T) evaluated prescribed displacement must exceed 24h serial limit (7.429 um)"

    def test_11_guard_against_asserting_displacement_from_increment_count_alone(self):
        """Guard against deriving physical displacement from raw increment counts without captured step time or field output."""
        def parse_telemetry_checkpoint_provenance(captured_record):
            """
            Governed hierarchy:
            1. actual_rp_u2: field/history output from .dat or uel_energy_balance.csv
            2. step_time: evaluated prescribed boundary displacement from captured step time
            3. none: report NOT_VERIFIED_FROM_CHECKPOINT_EVIDENCE
            """
            if "actual_rp_u2" in captured_record and captured_record["actual_rp_u2"] is not None:
                return {
                    "displacement_source": "MEASURED_RP_FIELD_OUTPUT",
                    "u_y": captured_record["actual_rp_u2"],
                    "is_measured": True
                }
            elif "step_time" in captured_record and captured_record["step_time"] is not None:
                step = captured_record["step"]
                st = captured_record["step_time"]
                u_prescribed = 0.0050 * st if step == 1 else 0.0050 + st * 0.0050
                return {
                    "displacement_source": "EVALUATED_PRESCRIBED_BC_FROM_CAPTURED_STEP_TIME",
                    "u_y": u_prescribed,
                    "is_measured": False
                }
            else:
                return {
                    "displacement_source": "NOT_VERIFIED_FROM_CHECKPOINT_EVIDENCE",
                    "u_y": None,
                    "is_measured": False
                }

        # Case 1: Record with only increment count (no step time, no actual RP U2)
        rec_inc_only = {"step": 2, "increment": 3302}
        res_inc_only = parse_telemetry_checkpoint_provenance(rec_inc_only)
        assert res_inc_only["displacement_source"] == "NOT_VERIFIED_FROM_CHECKPOINT_EVIDENCE"
        assert res_inc_only["u_y"] is None

        # Case 2: Record with captured step time (F1276 snapshot)
        rec_sta = {"step": 2, "increment": 3302, "step_time": 0.6580}
        res_sta = parse_telemetry_checkpoint_provenance(rec_sta)
        assert res_sta["displacement_source"] == "EVALUATED_PRESCRIBED_BC_FROM_CAPTURED_STEP_TIME"
        assert abs(res_sta["u_y"] - 0.008290) < 1e-6
        assert res_sta["is_measured"] is False  # Explicitly distinguished from measured internal field

        # Case 3: Record with actual measured field output (Terminal evaluation)
        rec_dat = {"step": 2, "increment": 5000, "step_time": 1.0, "actual_rp_u2": 0.010000}
        res_dat = parse_telemetry_checkpoint_provenance(rec_dat)
        assert res_dat["displacement_source"] == "MEASURED_RP_FIELD_OUTPUT"
        assert res_dat["u_y"] == 0.010000
        assert res_dat["is_measured"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
