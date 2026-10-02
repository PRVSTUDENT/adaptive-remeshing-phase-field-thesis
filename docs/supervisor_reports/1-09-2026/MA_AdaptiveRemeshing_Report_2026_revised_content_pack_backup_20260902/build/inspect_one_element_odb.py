from odbAccess import openOdb

odb = openOdb(path=r"D:\Master thesis\Adaptive remeshing\runs\molnar_one_element_unchanged\20260714_technical_gate_local\evidence\OneElement.odb", readOnly=True)
print("STEPS", list(odb.steps.keys()))
for step_name, step in odb.steps.items():
    print("STEP", step_name, "FRAMES", len(step.frames))
    if step.frames:
        print("FIELDS", sorted(step.frames[-1].fieldOutputs.keys()))
odb.close()
