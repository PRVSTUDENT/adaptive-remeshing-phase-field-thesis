from odbAccess import openOdb

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps["Step-1"]
print("ALL FRAMES:")
for i, f in enumerate(step.frames):
    print("Frame %2d: id=%3d, t=%.6f, u_top=%.6f" % (i, f.frameId, float(f.frameValue), float(f.frameValue)*0.005))

odb.close()
