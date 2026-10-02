#!/usr/bin/env python3
"""
Extract Node 99999 entries from DAT file.
"""

import json
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent.parent.parent / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02"
DAT_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R7.dat"

def parse_exact():
    records = []
    
    with open(DAT_PATH, "r", errors="ignore") as f:
        for line in f:
            if line.strip().startswith("99999"):
                parts = line.split()
                # format: 99999 [footnote] U1 U2 U3 RF1 RF2 RF3
                # or: 99999 U1 U2 U3 RF1 RF2 RF3
                nums = []
                for p in parts[1:]:
                    try:
                        nums.append(float(p))
                    except ValueError:
                        pass
                if len(nums) >= 5:
                    u1 = nums[0]
                    u2 = nums[1]
                    u3 = nums[2]
                    rf1 = nums[3]
                    rf2 = nums[4]
                    records.append({
                        "frame_index": len(records),
                        "u1_rp_mm": u1,
                        "u2_rp_mm": u2,
                        "u3_rp": u3,
                        "rf1_rp_kN": rf1,
                        "rf2_rp_kN": rf2
                    })

    print(f"Extracted {len(records)} RP frames from DAT file.")
    if records:
        print(f"Step 1 RP: U1={records[0]['u1_rp_mm']:.6f} mm, RF1={records[0]['rf1_rp_kN']:.6f} kN")
        print(f"Step 2 Frame 1: U1={records[1]['u1_rp_mm']:.6f} mm, RF1={records[1]['rf1_rp_kN']:.6f} kN")
        print(f"Step 2 Final Frame: U1={records[-1]['u1_rp_mm']:.6f} mm, RF1={records[-1]['rf1_rp_kN']:.6f} kN")
        
        rf1_vals = [r['rf1_rp_kN'] for r in records]
        max_rf1 = max(rf1_vals)
        max_idx = rf1_vals.index(max_rf1)
        print(f"Peak Reaction Force RF1: {max_rf1:.6f} kN at U1 = {records[max_idx]['u1_rp_mm']:.6f} mm (Frame {max_idx})")
        
        with open(EVIDENCE_DIR / "RP_FORCE_DISPLACEMENT_CURVE.json", "w") as f:
            json.dump(records, f, indent=2)

if __name__ == "__main__":
    parse_exact()
