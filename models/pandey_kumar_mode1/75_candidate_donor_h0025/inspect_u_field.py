from odbAccess import openOdb

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps["Step-1"]
f22 = step.frames[22]
u_field = f22.fieldOutputs["U"]
print("U field type: %s, components: %s" % (u_field.type, u_field.componentLabels))
print("Number of values in U: %d" % len(u_field.values))
first_val = u_field.values[0]
print("Node %d: data len=%d, data=%s" % (first_val.nodeLabel, len(first_val.data), first_val.data))

# Check max U1, U2, and if U3 exists
has_u3 = False
max_u1 = -1e9; max_u2 = -1e9; max_u3 = -1e9
for v in u_field.values:
    d = v.data
    if len(d) >= 1 and d[0] > max_u1: max_u1 = d[0]
    if len(d) >= 2 and d[1] > max_u2: max_u2 = d[1]
    if len(d) >= 3:
        has_u3 = True
        if d[2] > max_u3: max_u3 = d[2]

print("has_u3: %s" % has_u3)
print("max_u1: %g, max_u2: %g, max_u3: %g" % (max_u1, max_u2, max_u3))

odb.close()
