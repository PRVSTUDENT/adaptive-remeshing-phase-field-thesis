from odbAccess import openOdb

def inspect_test_odb():
    odb = openOdb("/home/pr21vyci/test_equation_semantics.odb", readOnly=True)
    step = odb.steps["Step-1"]
    frame = step.frames[-1]
    u = frame.fieldOutputs["U"]
    for v in u.values:
        print("Node %d: U1=%f, U2=%f" % (v.nodeLabel, v.data[0], v.data[1]))
    odb.close()

if __name__ == "__main__":
    inspect_test_odb()
