#!/usr/bin/env python3
"""
F137QUAL PK10R1 Continuous (1389684) Handoff Frame Enumeration & Selection
Task ID: F137QUAL-M2-PK10R1-SAMEMESH-RESTART-HANDOFF-FREEZE1
"""

import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "scripts/postprocessing/f136_data.json"

def main():
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} does not exist!")
        return
        
    data = json.loads(DATA_FILE.read_text())
    pk10 = data["pk10"]
    
    print("================================================================================")
    print("F137QUAL PK10R1 CONTINUOUS (1389684) ACCEPTED FRAMES ENUMERATION")
    print("Neighborhood: 0.00035 <= RP_U1 <= 0.00055 mm")
    print("================================================================================")
    print(f"{'Step':<5} | {'Inc':<5} | {'Step Time':<12} | {'RP U1 (mm)':<12} | {'RP RF1 (kN)':<12} | {'dmax':<10} | {'Hmax':<10}")
    print("-" * 80)
    
    target_frames = []
    
    for f in pk10:
        u1 = f["u1"]
        if 0.00035 <= u1 <= 0.00055:
            target_frames.append(f)
            print(f"{1:<5} | {f['inc']:<5} | {f['step_time']:<12.6f} | {f['u1']:<12.6f} | {f['rf1']:<12.6f} | {f['dmax']:<10.4f} | {f['hmax']:<10.4f}")

    print("\n--- Frame Selection Criteria Analysis ---")
    print("Target dmax: ~0.20 to 0.30 in pre-peak damaged regime")
    
    best_frame = None
    min_diff = 999.0
    for f in target_frames:
        diff = abs(f["dmax"] - 0.25)
        if diff < min_diff:
            min_diff = diff
            best_frame = f
            
    print(f"\nSELECTED EXACT ACCEPTED FRAME:")
    print(f"  source_step = 1")
    print(f"  source_increment = {best_frame['inc']}")
    print(f"  source_step_time = {best_frame['step_time']:.6f}")
    print(f"  source_RP_U1_mm = {best_frame['u1']:.6f}")
    print(f"  source_RP_RF1_kN = {best_frame['rf1']:.6f}")
    print(f"  source_dmax = {best_frame['dmax']:.6f}")
    print(f"  source_Hmax = {best_frame['hmax']:.6f}")

if __name__ == "__main__":
    main()
