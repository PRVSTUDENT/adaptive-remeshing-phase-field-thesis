# Inspect all field outputs in ODB
from odbAccess import openOdb
import sys, math

def inspect_odb_fields():
    odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.odb"
    odb = openOdb(odb_path, readOnly=True)
    
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        print("=== STEP: %s ===" % step_name)
        for fi, frame in enumerate([step.frames[0], step.frames[-1]]):
            print("  Frame %d (time=%.6f):" % (fi, frame.frameValue))
            print("    Field Outputs: %s" % list(frame.fieldOutputs.keys()))
            for fld_name in frame.fieldOutputs.keys():
                fld = frame.fieldOutputs[fld_name]
                print("    Field: %s (type=%s, locations=%d)" % (fld_name, str(fld.type), len(fld.values)))
                # Check first 5 values
                count = 0
                for v in fld.values:
                    data = v.data
                    print("      loc=%s val=%s" % (str(v.nodeLabel if hasattr(v, 'nodeLabel') else v.elementLabel), str(data)))
                    count += 1
                    if count >= 5:
                        break

    odb.close()

if __name__ == "__main__":
    inspect_odb_fields()
