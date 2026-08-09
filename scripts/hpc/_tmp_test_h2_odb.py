from odbAccess import openOdb
import sys

odb_path = "/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h2_serial_1379578.mmaster02/ModeII_H2_uniform_serial.odb"
odb = openOdb(odb_path, readOnly=True)

print("Assembly nodeSets:", list(odb.rootAssembly.nodeSets.keys()))
for inst_name, inst in odb.rootAssembly.instances.items():
    print("Instance %s nodeSets: %s" % (inst_name, list(inst.nodeSets.keys())))

# Check U and RF in Step-1 and Step-2
for sname, step in odb.steps.items():
    f0 = step.frames[0]
    flast = step.frames[-1]
    print("Step %s (frame 0 time %f to frame %d time %f):" % (sname, f0.frameValue, len(step.frames)-1, flast.frameValue))
    if "U" in flast.fieldOutputs:
        u_fo = flast.fieldOutputs["U"]
        print("  U field values len: %d" % len(u_fo.values))
        for nset_name in ["RP", "RP_U1", "REF_POINT", "TOP_DISP"]:
            if nset_name in odb.rootAssembly.nodeSets:
                nset = odb.rootAssembly.nodeSets[nset_name]
                usub = u_fo.getSubset(region=nset)
                if len(usub.values) > 0:
                    print("  U at %s: %s" % (nset_name, str(usub.values[0].data)))

odb.close()
