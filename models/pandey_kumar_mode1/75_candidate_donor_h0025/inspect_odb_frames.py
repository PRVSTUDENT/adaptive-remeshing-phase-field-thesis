from odbAccess import openOdb
import sys

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)

print("Step names: %s" % list(odb.steps.keys()))
step = odb.steps["Step-1"]
print("Total frames: %d" % len(step.frames))

# Print frame values around time 0.508
print("Frames around t=0.508:")
for i, f in enumerate(step.frames):
    t = float(f.frameValue)
    if 0.49 <= t <= 0.52:
        print("Frame %d: frameId=%d, value=%.6f, desc='%s'" % (i, f.frameId, t, f.description))

# Also check history regions
print("History regions:")
for hr_name in list(step.historyRegions.keys()):
    hr = step.historyRegions[hr_name]
    print("  Region: %s, outputs: %s" % (hr_name, list(hr.historyOutputs.keys())))

# Check fieldOutputs in frame 0 and last frame
print("Field outputs in frame 0: %s" % list(step.frames[0].fieldOutputs.keys()))
if len(step.frames) > 1:
    print("Field outputs in frame 1: %s" % list(step.frames[1].fieldOutputs.keys()))

odb.close()
