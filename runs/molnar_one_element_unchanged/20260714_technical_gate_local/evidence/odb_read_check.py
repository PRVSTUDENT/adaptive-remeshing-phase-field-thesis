from odbAccess import openOdb
odb_path = r"D:\Master thesis\Adaptive remeshing\runs\molnar_one_element_unchanged\20260714_technical_gate_local\work\OneElement.odb"
odb = openOdb(path=odb_path, readOnly=True)
print('ODB_READABLE: yes')
print('ODB_PATH:', odb_path)
print('STEPS:', ','.join(odb.steps.keys()))
for step_name, step in odb.steps.items():
    print('STEP %s FRAMES %d' % (step_name, len(step.frames)))
    if step.frames:
        frame = step.frames[-1]
        print('STEP %s LAST_FRAME_VALUE %s' % (step_name, frame.frameValue))
        print('STEP %s FIELD_OUTPUTS %s' % (step_name, ','.join(sorted(frame.fieldOutputs.keys()))))
odb.close()