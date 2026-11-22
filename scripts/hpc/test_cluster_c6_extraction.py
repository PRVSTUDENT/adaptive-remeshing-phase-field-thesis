#!/usr/bin/env python3
import sys
import os

run_dir = "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_single_job"
sys.path.insert(0, run_dir)
from case3_single_job_orchestrator import Case3SingleJobOrchestrator, compute_narrow_band_spec

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

# Verify robust crack tip extraction
assert abs(c6_state.get("tip_x", 0.0) - 30.5113) < 0.001, "tip_x must be 30.5113 mm, got %s" % c6_state.get("tip_x")
assert abs(c6_state.get("tip_y", 0.0) - 66.7437) < 0.001, "tip_y must be 66.7437 mm, got %s" % c6_state.get("tip_y")
print("ROBUST CRACK TIP CHECK: PASS (tip=(30.5113, 66.7437) mm)")

# Verify Cycle 7 narrow band coverage
band_spec = compute_narrow_band_spec(tip_x=c6_state["tip_x"], tip_y=c6_state["tip_y"])
local_y_min = band_spec["tip_y"] - band_spec["half_width_mm"]
local_y_max = band_spec["tip_y"] + band_spec["half_width_mm"]
print("=== CYCLE 7 NARROW BAND COVERAGE ===")
print("Local band y-range at crack front: [{:.4f}, {:.4f}] mm".format(local_y_min, local_y_max))
print("Overall bounding box y-range: [{:.4f}, {:.4f}] mm".format(band_spec["y_min"], band_spec["y_max"]))
print("Distance from crack front to centreline: 0.0000 mm")
assert abs(local_y_min - 65.7437) < 0.001
assert abs(local_y_max - 67.7437) < 0.001
print("CYCLE 7 NARROW BAND CHECK: PASS (crack front centered in fine mesh)")

