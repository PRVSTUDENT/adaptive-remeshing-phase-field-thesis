#!/usr/bin/env python3
import sys
import os

run_dir = "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_single_job"
sys.path.insert(0, run_dir)
from case3_single_job_orchestrator import Case3SingleJobOrchestrator

orch = Case3SingleJobOrchestrator(run_dir=run_dir, n_adaptive_steps=100)
c6_state = orch.extract_cycle_state("PK_METHOD_C_CASE3_CYCLE6")

print("=== REAL CLUSTER ORCHESTRATOR EXTRACTION: CYCLE 6 ===")
print("terminal_u2 :", c6_state.get("terminal_u2"))
print("tip_x       :", c6_state.get("tip_x"))
print("tip_y       :", c6_state.get("tip_y"))
print("max_damage  :", c6_state.get("max_damage"))
print("terminal_rf2:", c6_state.get("terminal_rf2"))

# Simulate resume calculation
actual_u2 = c6_state.get("terminal_u2")
nominal_u2 = round(orch.coarse_u2_mm + 6 * orch.load_increment_mm, 4)
donor_u2 = round(float(actual_u2), 4) if (actual_u2 is not None and actual_u2 > 0.0) else nominal_u2

print("=== RESUME CALCULATION ===")
print("Nominal donor u2 (old formula): {:.4f} mm".format(nominal_u2))
print("Actual donor u2  (new formula): {:.4f} mm".format(donor_u2))
assert donor_u2 == 0.1000, "donor_u2 must be exactly 0.1000 mm"
print("RESUME LOAD CHECK: PASS (donor_u2 == 0.1000 mm)")
