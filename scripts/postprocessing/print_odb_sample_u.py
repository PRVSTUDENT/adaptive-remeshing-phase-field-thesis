from odbAccess import openOdb

odb = openOdb("M2STATE_FRACFIX_RESTART2R4.odb", readOnly=True)
s1 = odb.steps['Step-1-PhaseInit']
f1 = s1.frames[1]
u = f1.fieldOutputs['U']

print "=== SAMPLE NODES IN STEP 1 FRAME 1 ==="
count = 0
for v in u.values:
    print "Node %d: %s" % (v.nodeLabel, str(v.data))
    count += 1
    if count >= 20:
        break

print "\n=== TOP NODES IN STEP 1 FRAME 1 ==="
for v in u.values:
    if v.nodeLabel > 9700 and v.nodeLabel <= 9720:
        print "Node %d: %s" % (v.nodeLabel, str(v.data))

odb.close()
