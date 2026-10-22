from odbAccess import openOdb

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps["Step-1"]
f22 = step.frames[22]
rf_field = f22.fieldOutputs["RF"]
print("RF field type: %s, components: %s" % (rf_field.type, rf_field.componentLabels))
print("Number of values in RF: %d" % len(rf_field.values))
first_val = rf_field.values[0]
print("Node %d: data len=%d, data=%s" % (first_val.nodeLabel, len(first_val.data), first_val.data))
odb.close()
