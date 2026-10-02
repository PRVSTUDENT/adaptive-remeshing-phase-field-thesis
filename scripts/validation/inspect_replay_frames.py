from odbAccess import openOdb
import sys

odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps.values()[0]

print("Total Frames in ODB: %d" % len(step.frames))
print("Listing Frames 0 to 30:")
for idx in range(min(31, len(step.frames))):
    f = step.frames[idx]
    if 'U' in f.fieldOutputs:
        u_field = f.fieldOutputs['U']
        num_u = len(u_field.values)
    else:
        num_u = 0
    print("Frame %2d: desc='%s', time=%.8f, U_nodes=%d" % (idx, f.description, f.frameValue, num_u))

odb.close()
