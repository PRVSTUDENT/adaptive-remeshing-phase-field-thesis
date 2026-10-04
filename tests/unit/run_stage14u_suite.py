#!/usr/bin/env python3
"""
Comprehensive Test Runner for Stage-14U Test Suite
--------------------------------------------------
Discovers and executes all Stage-14U test modules in tests/unit/.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def run_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    unit_dir = os.path.dirname(os.path.abspath(__file__))
    if unit_dir not in sys.path:
        sys.path.insert(0, unit_dir)
    
    stage14u_test_files = [
        "test_stage14u_completion_job.py",
        "test_stage14up_control_parity.py",
        "test_stage14uq_evaluator_certification.py",
        "test_stage14ur_temporal_convergence_preflight.py",
        "test_stage14ut_spatial_convergence_audit.py",
        "test_stage14uu_spatial_convergence_provenance.py",
        "test_stage14uv_energy_evolution_audit.py",
        "test_stage14uw_energy_claims_discipline.py",
        "test_stage14ux_spatial_provenance_and_convergence.py",
        "test_stage14uy_adaptive_spatial_sensitivity.py",
        "test_stage14uz_length_scale_sensitivity.py",
        "test_stage14uah_convergence_reconstruction.py",
        "test_stage14uai_claim_correction_and_parity.py",
        "test_stage14uaj_crossing_and_terminal_parity.py",
        "test_stage14uak_stage_b_determinism.py",
        "test_stage14ual_evaluators_and_protocols.py"
    ]
    
    for fname in stage14u_test_files:
        fpath = os.path.join(unit_dir, fname)
        if os.path.exists(fpath):
            mod_name = fname[:-3]
            try:
                mod = __import__(mod_name)
                tests = loader.loadTestsFromModule(mod)
                suite.addTests(tests)
            except Exception as e:
                print(f"[ERROR] Loading {mod_name}: {e}")
        else:
            print(f"[WARNING] Test file not found: {fname}")
            
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print(f"Stage-14U Suite Summary: {result.testsRun} tests run, {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_suite())
