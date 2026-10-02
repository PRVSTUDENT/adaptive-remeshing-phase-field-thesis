#!/usr/bin/env python3
"""
F181 Native Restart Equivalence Analysis
Compare 1389718 native restart against 1389677/1389707 uninterrupted continuous reference.
"""

import math
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_control_batch/evidence"
NATIVE_JSON = EVIDENCE_DIR / "1389718.mmaster02/exact_rp_trajectory.json"
CONTINUOUS_JSON = EVIDENCE_DIR / "CONTROL_BATCH_REPLACEMENT_EXTRACTED_RESULTS.json"

def main():
    with open(NATIVE_JSON) as f:
        native_records = json.load(f)

    with open(CONTINUOUS_JSON) as f:
        cont_data = json.load(f)

    cont_frames = cont_data["PK10R1_CONTINUOUS_U050"]["frames"]

    # Filter native records for ShearStep (which corresponds to Step 1 continuation)
    native_shear = [r for r in native_records if r["step"] == "ShearStep"]

    # Match frames by u1 displacement (within 1e-6 mm)
    matched_ref_rf = []
    matched_native_rf = []
    matched_u1 = []

    for nr in native_shear:
        u_nat = nr["u1_mm"]
        rf_nat = nr["rf1_kN"]
        # Find matching frame in continuous reference
        matches = [cf for cf in cont_frames if abs(cf["u1"] - u_nat) < 1e-6]
        if matches:
            cf = matches[0]
            matched_ref_rf.append(cf["rf1"])
            matched_native_rf.append(rf_nat)
            matched_u1.append(u_nat)

    abs_errs = [abs(nat - ref) for nat, ref in zip(matched_native_rf, matched_ref_rf)]
    rel_errs = [abs(nat - ref) / abs(ref) for nat, ref in zip(matched_native_rf, matched_ref_rf) if ref != 0]

    # Relative L2 Error = ||RF_native - RF_ref||_2 / ||RF_ref||_2
    l2_num = math.sqrt(sum((nat - ref)**2 for nat, ref in zip(matched_native_rf, matched_ref_rf)))
    l2_den = math.sqrt(sum(ref**2 for ref in matched_ref_rf))
    l2_err = l2_num / l2_den if l2_den > 0 else 0.0

    max_abs_err = max(abs_errs) if abs_errs else 0.0
    max_rel_err = max(rel_errs) if rel_errs else 0.0

    # Peak values across entire continuous trajectory vs native restart segment
    peak_rf_ref = max(cf["rf1"] for cf in cont_frames)
    peak_u1_ref = [cf["u1"] for cf in cont_frames if cf["rf1"] == peak_rf_ref][0]

    peak_rf_native_restart = max(r["rf1_kN"] for r in native_shear)
    peak_u1_native_restart = [r["u1_mm"] for r in native_shear if r["rf1_kN"] == peak_rf_native_restart][0]

    peak_rf_rel_err = abs(peak_rf_native_restart - peak_rf_ref) / peak_rf_ref if peak_rf_ref > 0 else 0.0
    peak_u_rel_err = abs(peak_u1_native_restart - peak_u1_ref) / peak_u1_ref if peak_u1_ref > 0 else 0.0

    print("================================================================================")
    print("F181 INDEPENDENT NATIVE-RESTART EQUIVALENCE QUANTIFICATION")
    print("================================================================================")
    print("Matched points in overlapping range (u1 >= 0.01064 mm): {0}".format(len(matched_u1)))
    print("native_restart_RF_relative_L2_error = {0:.6e}".format(l2_err))
    print("native_restart_RF_max_abs_error      = {0:.6e} kN ({1:.6f} N)".format(max_abs_err, max_abs_err * 1000.0))
    print("native_restart_RF_max_relative_error = {0:.6e} ({1:.4f}%)".format(max_rel_err, max_rel_err * 100.0))
    print("native_restart_peak_RF1              = {0:.6f} kN (at u1 = {1:.6f} mm)".format(peak_rf_native_restart, peak_u1_native_restart))
    print("uninterrupted_peak_RF1               = {0:.6f} kN (at u1 = {1:.6f} mm)".format(peak_rf_ref, peak_u1_ref))
    print("peak_RF_relative_error              = {0:.6e}".format(peak_rf_rel_err))
    print("peak_U_relative_error               = {0:.6e}".format(peak_u_rel_err))

if __name__ == "__main__":
    main()

