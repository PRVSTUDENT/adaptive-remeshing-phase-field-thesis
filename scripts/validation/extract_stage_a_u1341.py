from odbAccess import openOdb

odb = openOdb("M1_C3_STAGGERED_R6.odb", readOnly=True)
step1 = odb.steps["Stage-A"]
frame1 = step1.frames[-1]

u_field = frame1.fieldOutputs['U']
nodes_to_check = [1366, 1367, 1421, 1420]

print("Converged Nodal Displacements of Element 1341 in Stage-A:")
for val in u_field.values:
    if val.nodeLabel in nodes_to_check:
        print("  Node %d: U1=%.9e, U2=%.9e, U3=%.9e" % (val.nodeLabel, val.data[0], val.data[1], val.data[2] if len(val.data)>2 else 0.0))

odb.close()
