#!/usr/bin/env python
import sys
import os
from odbAccess import openOdb

def main():
    odb_path = sys.argv[1] if len(sys.argv) > 1 else "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.odb"
    print("=== Raw ODB Field Truth Audit: %s ===" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    for step_name in sorted(odb.steps.keys()):
        step = odb.steps[step_name]
        print("\nStep: %s (Total Frames: %d)" % (step_name, len(step.frames)))
        
        for fid in range(len(step.frames)):
            frame = step.frames[fid]
            # Print details if first, last, or if any field has > 1e-12
            s14_info = s15_info = s16_info = ""
            has_nonzero = False
            
            for var_name in ['SDV14', 'SDV15', 'SDV16']:
                if var_name in frame.fieldOutputs:
                    vals = [float(v.data[0] if hasattr(v.data, '__getitem__') else v.data) for v in frame.fieldOutputs[var_name].values]
                    if vals:
                        v_min = min(vals)
                        v_max = max(vals)
                        c_12 = sum(1 for v in vals if v > 1e-12)
                        c_10 = sum(1 for v in vals if v > 1e-10)
                        c_8  = sum(1 for v in vals if v > 1e-8)
                        c_6  = sum(1 for v in vals if v > 1e-6)
                        c_4  = sum(1 for v in vals if v > 1e-4)
                        c_3  = sum(1 for v in vals if v > 1e-3)
                        c_2  = sum(1 for v in vals if v > 1e-2)
                        c_01 = sum(1 for v in vals if v > 0.1)
                        c_05 = sum(1 for v in vals if v > 0.5)
                        if c_12 > 0:
                            has_nonzero = True
                        info_str = "%s: min=%.4e, max=%.4e [>1e-12:%d, >1e-10:%d, >1e-8:%d, >1e-6:%d, >1e-4:%d, >0.1:%d, >0.5:%d]" % (
                            var_name, v_min, v_max, c_12, c_10, c_8, c_6, c_4, c_01, c_05)
                        if var_name == 'SDV14': s14_info = info_str
                        elif var_name == 'SDV15': s15_info = info_str
                        elif var_name == 'SDV16': s16_info = info_str
            
            if fid == 0 or fid == len(step.frames) - 1 or has_nonzero:
                print("  Frame %d (t=%.6f s):" % (fid, frame.frameValue))
                if s14_info: print("    " + s14_info)
                if s15_info: print("    " + s15_info)
                if s16_info: print("    " + s16_info)

    odb.close()

if __name__ == "__main__":
    main()
