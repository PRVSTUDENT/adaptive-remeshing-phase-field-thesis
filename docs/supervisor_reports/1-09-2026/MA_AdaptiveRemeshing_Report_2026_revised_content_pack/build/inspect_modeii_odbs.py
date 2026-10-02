from odbAccess import openOdb

paths = (
    r"D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\reference_convergence\M2REF_H1\M2REF_H1.odb",
    r"D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\reference_convergence\M2REF_H2\M2REF_H2.odb",
)
for path in paths:
    odb = openOdb(path=path, readOnly=True)
    print("ODB", path)
    for name, instance in odb.rootAssembly.instances.items():
        counts = {}
        for element in instance.elements:
            counts[element.type] = counts.get(element.type, 0) + 1
        print("INSTANCE", name, "NODES", len(instance.nodes), "ELEMENTS", len(instance.elements), "TYPES", counts)
    for step_name, step in odb.steps.items():
        print("STEP", step_name, "FRAMES", len(step.frames), "END", step.frames[-1].frameValue)
        for frame_id in (0, len(step.frames)//2, len(step.frames)-1):
            frame = step.frames[frame_id]
            print("FRAME", frame_id, frame.frameValue, sorted(frame.fieldOutputs.keys()))
            for variable in ("SDV1", "SDV13", "SDV15"):
                values = [value.data for value in frame.fieldOutputs[variable].values]
                print("RANGE", variable, min(values), max(values))
    odb.close()
