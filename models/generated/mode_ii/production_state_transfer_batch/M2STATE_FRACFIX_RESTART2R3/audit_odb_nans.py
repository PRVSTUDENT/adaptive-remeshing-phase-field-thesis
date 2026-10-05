from odbAccess import openOdb
import math

odb = openOdb("M2STATE_FRACFIX_RESTART2R3.odb", readOnly=True)

for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    print "Step:", step_name
    for f_idx, f in enumerate(step.frames):
        if "U" in f.fieldOutputs:
            u_field = f.fieldOutputs["U"]
            nan_nodes = []
            finite_nodes = []
            for val in u_field.values:
                # check if any component is NaN
                has_nan = False
                for c in val.data:
                    if math.isnan(c) or math.isinf(c):
                        has_nan = True
                        break
                if has_nan:
                    nan_nodes.append((val.nodeLabel, val.data))
                else:
                    finite_nodes.append((val.nodeLabel, val.data))
            
            print "  Frame %d (t=%f): Total nodes=%d, Finite nodes=%d, NaN nodes=%d" % (
                f_idx, f.frameValue, len(u_field.values), len(finite_nodes), len(nan_nodes))
            if finite_nodes:
                print "    Sample finite:", finite_nodes[:3]
            if nan_nodes:
                print "    Sample NaN:", nan_nodes[:3]

odb.close()
