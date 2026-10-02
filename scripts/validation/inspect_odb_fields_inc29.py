from odbAccess import openOdb
import sys

odb_path = "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb"
if len(sys.argv) > 1:
    odb_path = sys.argv[1]

odb = openOdb(odb_path, readOnly=True)
print("=== ODB FIELD INSPECTION ===")
print("Steps:", odb.steps.keys())
step = odb.steps.values()[0]
print("Total Frames:", len(step.frames))
frame29 = step.frames[29]
print("Frame 29 description:", frame29.description, "time:", frame29.frameValue)
print("Field Outputs in Frame 29:")
for k in frame29.fieldOutputs.keys():
    fo = frame29.fieldOutputs[k]
    print("  Field:", k, "type:", fo.type, "locations:", len(fo.locations))
odb.close()
