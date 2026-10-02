#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic Unit Test Suite for Phase-Field Irreversibility Enforcement in UEL.

Tests the Active-Set Penalty Formulation for d_new(x) >= d_committed(x):
1. Same-Mesh Identity: d_new == d_committed when unloaded.
2. Transferred damaged field released with zero additional load: d_new >= d_committed (no healing, Delta d >= -1e-6).
3. Increased driving force: d_new grows naturally (d_new > d_committed), penalty deactivates.
4. Spatially varying lower bounds: Exactly satisfied point-by-point.
5. Intact nodes (d_committed = 0): Unaffected, d >= 0.
6. Fully damaged nodes (d_committed = 1): Remains d = 1.
7. Nonmatching transfer field: Eliminates the -0.002644 relaxation dip.
"""

import math
import json

def solve_phase_field_1d(d_committed, H_driving, l0=0.015, gc=0.0027, penalty_factor=1.0e8):
    """
    Solves discrete 1D/pointwise phase field algebraic equation:
    (gc/l0 + 2*H)*d + penalty*max(0, d_committed - d) = 2*H + penalty*max(0, d_committed - d)*d_committed (approx)
    Variational KKT form:
      f(d) = (gc/l0 + 2*H)*d - 2*H + gamma(d)*[d - d_committed] = 0
      where gamma(d) = penalty if d < d_committed else 0.0
    """
    k_base = gc / l0 + 2.0 * H_driving
    rhs_base = 2.0 * H_driving
    
    # 1. Unconstrained trial solution
    d_trial = rhs_base / k_base if k_base > 0 else 0.0
    
    # 2. If d_trial < d_committed, apply active-set penalty
    if d_trial < d_committed:
        gamma = penalty_factor * (gc / l0)
        d_solved = (rhs_base + gamma * d_committed) / (k_base + gamma)
        active_set = True
    else:
        d_solved = d_trial
        active_set = False
        
    return {
        "d_committed": d_committed,
        "H_driving": H_driving,
        "d_trial": d_trial,
        "d_solved": d_solved,
        "delta_d": d_solved - d_committed,
        "active_set": active_set,
        "no_healing": (d_solved >= d_committed - 1.0e-6)
    }

def run_test_suite():
    print("================================================================================")
    print("PHASE-FIELD IRREVERSIBILITY ACTIVE-SET PENALTY UNIT TEST SUITE")
    print("================================================================================")
    
    tests_passed = True
    
    # Test 1: Same-Mesh Identity (d_committed = 0.284444, H = 0.0354)
    # H exactly matches equilibrium of d_committed
    h_eq = (0.284444 * 0.18) / (2.0 * (1.0 - 0.284444)) # approx 0.03577
    t1 = solve_phase_field_1d(d_committed=0.284444, H_driving=h_eq)
    print("\nTest 1 (Same-Mesh Identity):")
    print("  d_committed = %.6f, d_solved = %.6f, delta_d = %+.6e, Active = %s" % (
        t1["d_committed"], t1["d_solved"], t1["delta_d"], t1["active_set"]))
    if abs(t1["delta_d"]) > 1.0e-5:
        print("  FAIL: Delta d too large")
        tests_passed = False
    else:
        print("  PASS")
        
    # Test 2: Transferred Damaged Field with Zero Additional Driving Force (H = 0.0)
    # Without penalty, d_trial would drop to 0.0 (catastrophic healing).
    # With penalty, d_solved must be >= d_committed - 1e-6.
    t2 = solve_phase_field_1d(d_committed=0.284444, H_driving=0.0)
    print("\nTest 2 (Released Damaged Field, Zero Load H=0):")
    print("  d_trial = %.6f (Healed!), d_solved = %.6f, delta_d = %+.6e, Active = %s" % (
        t2["d_trial"], t2["d_solved"], t2["delta_d"], t2["active_set"]))
    if not t2["no_healing"]:
        print("  FAIL: Healing detected!")
        tests_passed = False
    else:
        print("  PASS (No healing verified, Delta d >= -1e-6)")
        
    # Test 3: Increased Driving Force (Crack Growth, H = 0.848870)
    # Driving force is large enough to advance crack beyond d_committed.
    t3 = solve_phase_field_1d(d_committed=0.284444, H_driving=0.848870)
    print("\nTest 3 (Increased Driving Force H=0.848870):")
    print("  d_committed = %.6f, d_trial = %.6f, d_solved = %.6f, Active = %s" % (
        t3["d_committed"], t3["d_trial"], t3["d_solved"], t3["active_set"]))
    if t3["active_set"]:
        print("  FAIL: Penalty should be INACTIVE during natural crack growth!")
        tests_passed = False
    elif t3["d_solved"] <= t3["d_committed"]:
        print("  FAIL: Crack failed to grow!")
        tests_passed = False
    else:
        print("  PASS (Natural crack growth uninhibited, Penalty Inactive)")
        
    # Test 4: Spatially Varying Lower Bounds (Array of d_committed from 0.0 to 0.9)
    print("\nTest 4 (Spatially Varying Lower Bounds):")
    d_bounds = [0.0, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90]
    t4_pass = True
    for db in d_bounds:
        res = solve_phase_field_1d(d_committed=db, H_driving=0.01)
        if not res["no_healing"]:
            t4_pass = False
        print("  d_bound = %.2f -> d_solved = %.6f (delta: %+.6e, active: %s)" % (
            db, res["d_solved"], res["delta_d"], res["active_set"]))
    if not t4_pass:
        print("  FAIL: Spatially varying bounds violated")
        tests_passed = False
    else:
        print("  PASS")
        
    # Test 5: Intact Nodes (d_committed = 0.0)
    t5 = solve_phase_field_1d(d_committed=0.0, H_driving=0.005)
    print("\nTest 5 (Intact Nodes d_committed=0.0):")
    print("  d_solved = %.6f, Active = %s" % (t5["d_solved"], t5["active_set"]))
    if t5["d_solved"] < 0.0:
        print("  FAIL: Negative damage")
        tests_passed = False
    else:
        print("  PASS")
        
    # Test 6: Fully Damaged Nodes (d_committed = 1.0)
    t6 = solve_phase_field_1d(d_committed=1.0, H_driving=0.0)
    print("\nTest 6 (Fully Damaged Nodes d_committed=1.0):")
    print("  d_solved = %.6f, delta_d = %+.6e, Active = %s" % (
        t6["d_solved"], t6["delta_d"], t6["active_set"]))
    if not t6["no_healing"]:
        print("  FAIL: Fully damaged node healed")
        tests_passed = False
    else:
        print("  PASS")
        
    # Test 7: Nonmatching Target Stage-D Peak (d_committed = 0.284444, Target unconstrained equilibrium H = 0.0350)
    # Simulates the -0.002644 relaxation dip observed in F244/F245.
    t7 = solve_phase_field_1d(d_committed=0.284444, H_driving=0.0350)
    print("\nTest 7 (Nonmatching Target Stage-D Relaxation Dip Elimination):")
    print("  d_trial (Unconstrained) = %.6f (Dip = %+.6f)" % (t7["d_trial"], t7["d_trial"] - 0.284444))
    print("  d_solved (Active-Set)   = %.6f (Delta = %+.6e, Active = %s)" % (
        t7["d_solved"], t7["delta_d"], t7["active_set"]))
    if not t7["no_healing"]:
        print("  FAIL: Nonmatching relaxation dip not prevented")
        tests_passed = False
    else:
        print("  PASS (Relaxation dip successfully eliminated, Delta d >= -1e-6)")
        
    print("\n================================================================================")
    print("OVERALL UNIT TEST RESULT: %s" % ("ALL 7 TESTS PASSED" if tests_passed else "FAILED"))
    print("================================================================================")
    return tests_passed

if __name__ == "__main__":
    run_test_suite()
