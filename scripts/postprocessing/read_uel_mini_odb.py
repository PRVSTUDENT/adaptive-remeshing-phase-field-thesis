from odbAccess import openOdb
import sys

def inspect_mini_odb():
    odb_name = sys.argv[1] if len(sys.argv) > 1 else "/home/pr21vyci/test_uel_mini.odb"
    odb = openOdb(odb_name, readOnly=True)
    step = odb.steps["Step-1-PhaseInit"]
    for fi, frame in enumerate(step.frames):
        print("--- Frame %d (time=%.4f) ---" % (fi, frame.frameValue))
        u = frame.fieldOutputs["U"]
        for v in u.values:
            print("  Node %d: U1=%s, U2=%s" % (v.nodeLabel, str(v.data[0]), str(v.data[1])))
    odb.close()

if __name__ == "__main__":
    inspect_mini_odb()
