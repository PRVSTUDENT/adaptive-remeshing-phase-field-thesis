# -*- coding: utf-8 -*-
"""
read_f1692_audit.py
===================
Inspects sampled frames in f1692_sec43_damage_and_miseseri_audit.json
"""
import json

def main():
    p = "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/f1692_sec43_damage_and_miseseri_audit.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    print("Number of steps in audit:", len(d["steps"]))
    for i, s in enumerate(d["steps"]):
        frames = s["sampled_frames"]
        print("Step %d: %d sampled frames" % (i+1, len(frames)))
        for fr in frames:
            f_idx = fr["frame_index"]
            f_val = fr["frame_value"]
            max_p = fr["max_damage_primary"]
            max_s = fr["max_damage_secondary"]
            max_e = fr.get("max_miseseri_primary", 0.0)
            max_e_s = fr.get("max_miseseri_secondary", 0.0)
            print("  Frame %3d (t=%.4f): max_d_p=%.4f, max_d_s=%.4f, max_eri_p=%.1f, max_eri_s=%.1f" % (
                f_idx, f_val, max_p, max_s, max_e, max_e_s))

if __name__ == "__main__":
    main()
