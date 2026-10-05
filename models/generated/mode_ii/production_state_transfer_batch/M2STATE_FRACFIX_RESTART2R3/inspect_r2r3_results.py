import sys, os
from odbAccess import openOdb

def main():
    odb_path = "M2STATE_FRACFIX_RESTART2R3.odb"
    if not os.path.exists(odb_path):
        print "ERROR: ODB file not found:", odb_path
        return

    odb = openOdb(odb_path, readOnly=True)
    print "=== ODB SUMMARY ==="
    print "Steps in ODB:", odb.steps.keys()
    
    for sname, step in odb.steps.items():
        print "\nStep: %s (Total Frames: %d)" % (sname, len(step.frames))
        for f_idx in range(len(step.frames)):
            f = step.frames[f_idx]
            time_val = f.frameValue
            if "U" in f.fieldOutputs:
                u_field = f.fieldOutputs["U"]
                u1_vals = [v.data[0] for v in u_field.values if len(v.data) >= 1]
                u2_vals = [v.data[1] for v in u_field.values if len(v.data) >= 2]
                u3_vals = [v.data[2] for v in u_field.values if len(v.data) >= 3]
                
                u1_min, u1_max = min(u1_vals), max(u1_vals)
                u2_min, u2_max = min(u2_vals), max(u2_vals)
                if u3_vals:
                    u3_info = "U3 (Phase) min/max: [%.6f, %.6f]" % (min(u3_vals), max(u3_vals))
                else:
                    u3_info = "U3 not present in U field"
                
                if f_idx in [0, 1, len(step.frames)-1] or f_idx % 5 == 0:
                    print "  Frame %2d (t=%.6f): U1=[%.6f, %.6f], U2=[%.6f, %.6f], %s" % (
                        f_idx, time_val, u1_min, u1_max, u2_min, u2_max, u3_info)

    # Check history outputs (Reaction force RF1)
    print "\n=== HISTORY OUTPUTS ==="
    for sname, step in odb.steps.items():
        print "Step %s History Regions: %s" % (sname, str(step.historyRegions.keys()[:5]))
        for hname, hreg in step.historyRegions.items():
            for hk in hreg.historyOutputs.keys():
                if "RF" in hk or "U" in hk:
                    data = hreg.historyOutputs[hk].data
                    print "  Region: %s, Key: %s, Points: %d, Start: %s, End: %s" % (
                        hname, hk, len(data), str(data[0]), str(data[-1]))

    odb.close()

if __name__ == "__main__":
    main()
