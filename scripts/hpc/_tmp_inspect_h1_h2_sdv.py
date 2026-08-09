from __future__ import print_function
import sys
from odbAccess import openOdb

def audit_sdv(odb_path):
    print("==================================================")
    print("Auditing ODB:", odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step2 = odb.steps[sorted(odb.steps.keys())[-1]]
    print("Steps:", list(odb.steps.keys()))
    print("Step 2 frames count:", len(step2.frames))

    # Check field names in frame 0 and last frame
    f0 = odb.steps[sorted(odb.steps.keys())[0]].frames[0]
    flast = step2.frames[-1]
    print("Frame 0 field outputs:", list(f0.fieldOutputs.keys()))
    print("Last frame field outputs:", list(flast.fieldOutputs.keys()))

    for step_name in sorted(odb.steps.keys()):
        step = odb.steps[step_name]
        print("\n--- Step: %s ---" % step_name)
        frames_to_check = [0, len(step.frames)//2, len(step.frames)-1]
        for fidx in frames_to_check:
            frame = step.frames[fidx]
            print("  Frame %d (time=%.4f):" % (fidx, frame.frameValue))
            for sdv_name in ["SDV14", "SDV15", "SDV16", "SDV1", "SDV2", "SDV3"]:
                if sdv_name in frame.fieldOutputs:
                    fo = frame.fieldOutputs[sdv_name]
                    vals = [float(v.data[0]) if hasattr(v.data, '__getitem__') else float(v.data) for v in fo.values]
                    if vals:
                        min_v = min(vals)
                        max_v = max(vals)
                        nonzero = sum(1 for v in vals if abs(v) > 1e-12)
                        print("    %s: min=%.6e, max=%.6e, total_values=%d, nonzero_count=%d" % (sdv_name, min_v, max_v, len(vals), nonzero))
                    else:
                        print("    %s: EMPTY values" % sdv_name)
                else:
                    print("    %s: NOT PRESENT in fieldOutputs" % sdv_name)

    odb.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audit_sdv(sys.argv[1])
