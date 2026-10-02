#!/usr/bin/env python3
"""
F182 Extract Peak Reaction Forces & Resolve Discrepancies
Extract RP U1 and RF1 for node 99999 across 1389684, 1389707, and 1389718.
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_control_batch/evidence"

def analyze_trajectory(records, name):
    print(f"=== {name} ===")
    step_names = set(r.get("step") for r in records)
    print(f"Steps: {step_names}, Total Frames: {len(records)}")

    for step_name in sorted(list(step_names)):
        step_recs = [r for r in records if r.get("step") == step_name]
        rfs = [r["rf1_kN"] if "rf1_kN" in r else r.get("rf1", 0.0) for r in step_recs]
        u1s = [r["u1_mm"] if "u1_mm" in r else r.get("u1", 0.0) for r in step_recs]

        # Positive peak RF1
        pos_rfs = [(rf, u1) for rf, u1 in zip(rfs, u1s) if rf > 0]
        if pos_rfs:
            peak_rf, peak_u1 = max(pos_rfs, key=lambda x: x[0])
        else:
            peak_rf, peak_u1 = 0.0, 0.0

        min_rf = min(rfs) if rfs else 0.0
        term_rf = rfs[-1] if rfs else 0.0
        term_u1 = u1s[-1] if u1s else 0.0

        print(f"  Step: {step_name}")
        print(f"    Frame count:           {len(step_recs)}")
        print(f"    Peak positive RF1:     {peak_rf:.6f} kN (at U1 = {peak_u1:.6f} mm)")
        print(f"    Minimum RF1:           {min_rf:.6f} kN")
        print(f"    Terminal RF1:          {term_rf:.6f} kN (at U1 = {term_u1:.6f} mm)")

def main():
    # 1389718
    f18_path = EVIDENCE_DIR / "1389718.mmaster02/exact_rp_trajectory.json"
    if f18_path.exists():
        with open(f18_path) as f:
            f18_data = json.load(f)
        analyze_trajectory(f18_data, "1389718.mmaster02 (Native Restart R2)")

    # 1389684 (continuous reference in CONTROL_BATCH_REPLACEMENT_EXTRACTED_RESULTS.json)
    cb_path = EVIDENCE_DIR / "CONTROL_BATCH_REPLACEMENT_EXTRACTED_RESULTS.json"
    if cb_path.exists():
        with open(cb_path) as f:
            cb_data = json.load(f)
        if "PK10R1_CONTINUOUS_U050" in cb_data:
            recs = cb_data["PK10R1_CONTINUOUS_U050"]["frames"]
            analyze_trajectory(recs, "1389684.mmaster02 / PK10R1_CONTINUOUS_U050")

if __name__ == "__main__":
    main()
