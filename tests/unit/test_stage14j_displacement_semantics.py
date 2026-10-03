"""
Unit tests for Stage 14J: Step-2 Displacement Semantics and Evaluator State-Coordinate Verification.

Verifies:
1. Multi-step displacement mapping under Abaqus RAMP boundary conditions:
   - Step 1: u(t_1) = t_1 * u_1_target
   - Step 2: u(t_2) = u_1_target + t_2 * (u_2_target - u_1_target)
   - Step 2 normalized time t_2 CANNOT be mistaken for total specimen displacement.
2. Invariance against non-zero Step 1 endpoints and step discretization changes.
3. Strict selection of matched-displacement states based on minimum distance to physical u_RP.
4. Correct mapping for all 10 canonical target displacements [0.0010 ... 0.0100] mm.
"""

import math
import pytest


def abaqus_ramp_displacement(step_name, step_time, u_step1_end=0.0050, u_step2_end=0.0100):
    """
    Computes total specimen displacement under Abaqus default RAMP boundary conditions.
    """
    if step_name == 'Step-1':
        return step_time * u_step1_end
    elif step_name == 'Step-2':
        return u_step1_end + step_time * (u_step2_end - u_step1_end)
    else:
        raise ValueError(f"Unknown step: {step_name}")


def match_closest_frame(target_u, frame_records):
    """
    Selects the frame record that minimizes |u_RP - target_u|.
    Ensures selection is based on actual physical displacement, not frame index or normalized step time.
    """
    best_record = None
    min_diff = float('inf')
    for rec in frame_records:
        diff = abs(rec['u_rp_mm'] - target_u)
        if diff < min_diff:
            min_diff = diff
            best_record = rec
    return best_record, min_diff


class TestStage14JDisplacementSemantics:

    def test_step2_normalized_time_rejection(self):
        """
        Demonstrates that Step-2 normalized time t_2 * u_final (e.g. 0.465 * 0.010 = 0.00465 mm)
        is mathematically wrong and strictly rejected when Step 1 has a non-zero endpoint.
        """
        u_step1_end = 0.0050  # 5 um
        u_step2_end = 0.0100  # 10 um
        t_step2 = 0.465

        # WRONG naive formula (multiplying normalized step-2 time by final displacement)
        u_wrong_naive = t_step2 * u_step2_end  # 0.00465 mm

        # CORRECT Abaqus RAMP displacement
        u_correct = abaqus_ramp_displacement('Step-2', t_step2, u_step1_end, u_step2_end)  # 0.007325 mm

        # The two values must diverge significantly
        discrepancy = abs(u_correct - u_wrong_naive)
        assert discrepancy > 0.0020, f"Discrepancy too small: {discrepancy}"
        assert math.isclose(u_correct, 0.007325, rel_tol=1e-6)
        assert math.isclose(u_wrong_naive, 0.004650, rel_tol=1e-6)

        # In Step 2, displacement must always be >= u_step1_end
        assert u_correct >= u_step1_end, f"Step 2 displacement {u_correct} cannot be less than Step 1 endpoint {u_step1_end}"
        assert u_wrong_naive < u_step1_end, "Naive calculation erroneously fell below Step 1 endpoint!"

    def test_canonical_reference_schedule_parity(self):
        """
        Verifies exact parity against the authoritative fixed reference schedule:
        - Step 1 final: u = 0.005000 mm (frame 2000)
        - Step 2 frame 857 (t=0.1714): u = 0.005857 mm (peak load)
        - Step 2 frame 1000 (t=0.2000): u = 0.006000 mm
        - Step 2 frame 5000 (t=1.0000): u = 0.010000 mm
        """
        # Step 1 final
        u_s1_end = abaqus_ramp_displacement('Step-1', 1.0, 0.0050, 0.0100)
        assert math.isclose(u_s1_end, 0.005000, abs_tol=1e-9)

        # Step 2 frame 857 (dt = 0.0002000 -> t = 857 * 0.0002 = 0.1714)
        t_f857 = 857 * 0.0002
        u_f857 = abaqus_ramp_displacement('Step-2', t_f857, 0.0050, 0.0100)
        assert math.isclose(u_f857, 0.005857, abs_tol=1e-6)

        # Step 2 frame 1000 (t = 1000 * 0.0002 = 0.2000)
        t_f1000 = 1000 * 0.0002
        u_f1000 = abaqus_ramp_displacement('Step-2', t_f1000, 0.0050, 0.0100)
        assert math.isclose(u_f1000, 0.006000, abs_tol=1e-6)

        # Step 2 frame 5000 (t = 1.0000)
        u_s2_end = abaqus_ramp_displacement('Step-2', 1.0, 0.0050, 0.0100)
        assert math.isclose(u_s2_end, 0.010000, abs_tol=1e-9)

    def test_ten_matched_states_selection_robustness(self):
        """
        Verifies that matching 10 target states from discrete frame records selects
        the correct step and frame regardless of non-uniform step sizes.
        """
        targets = [
            0.0010, 0.0020, 0.0030, 0.0040, 0.0050,
            0.005857, 0.0060, 0.0070, 0.0080, 0.0100
        ]

        # Construct synthetic frame records for Step 1 (dt=5e-4 -> 2000 frames) and Step 2 (dt=2e-4 -> 5000 frames)
        frames = []
        # Step 1
        for inc in range(2001):
            t = inc * 5.0e-4
            u = t * 0.0050
            frames.append({'step': 'Step-1', 'frame_idx': inc, 'step_time': t, 'u_rp_mm': u})

        # Step 2
        for inc in range(1, 5001):
            t = inc * 2.0e-4
            u = 0.0050 + t * 0.0050
            frames.append({'step': 'Step-2', 'frame_idx': inc, 'step_time': t, 'u_rp_mm': u})

        for u_target in targets:
            best_rec, diff = match_closest_frame(u_target, frames)
            assert diff <= 1.0e-6, f"Matching tolerance exceeded for target {u_target}: diff={diff}"
            if u_target <= 0.0050:
                assert best_rec['step'] == 'Step-1', f"Target {u_target} should be in Step-1"
            else:
                assert best_rec['step'] == 'Step-2', f"Target {u_target} should be in Step-2"

    def test_arbitrary_step1_endpoint_invariance(self):
        """
        Verifies formulation invariance when arbitrary Step 1 endpoint displacements are used.
        """
        u_step1_custom = 0.0035
        u_step2_custom = 0.0120

        # At t_step1 = 0.5 -> u = 0.5 * 0.0035 = 0.00175
        u1 = abaqus_ramp_displacement('Step-1', 0.5, u_step1_custom, u_step2_custom)
        assert math.isclose(u1, 0.00175, abs_tol=1e-9)

        # At t_step2 = 0.5 -> u = 0.0035 + 0.5 * (0.0120 - 0.0035) = 0.0035 + 0.00425 = 0.00775
        u2 = abaqus_ramp_displacement('Step-2', 0.5, u_step1_custom, u_step2_custom)
        assert math.isclose(u2, 0.00775, abs_tol=1e-9)
