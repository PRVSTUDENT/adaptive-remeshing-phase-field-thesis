from odbAccess import openOdb
import math

def inspect_r2r6_full_odb():
    odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6/M2STATE_FRACFIX_RESTART2R6.odb"
    odb = openOdb(odb_path, readOnly=True)
    
    print "Steps in ODB:", odb.steps.keys()
    for sname, step in odb.steps.items():
        print "\nStep:", sname, "Total frames:", len(step.frames)
        for fidx, frame in enumerate(step.frames):
            u = frame.fieldOutputs["U"]
            nan_count = 0
            max_u1 = 0.0
            for v in u.values:
                u1, u2 = v.data[0], v.data[1]
                if math.isnan(u1) or math.isnan(u2):
                    nan_count += 1
                if abs(u1) > max_u1:
                    max_u1 = abs(u1)
            print "  Frame %d (t=%.6f): values=%d, NaNs=%d, max|U1|=%.6f" % (fidx, frame.frameValue, len(u.values), nan_count, max_u1)
            
    odb.close()

if __name__ == "__main__":
    inspect_r2r6_full_odb()
