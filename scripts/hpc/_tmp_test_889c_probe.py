# -*- coding: utf-8 -*-
import sys
import traceback

print("=== ABAQUS 2023 PROBE STARTING FOR 889c15 CAE ===")

try:
    from abaqus import mdb
except Exception as e:
    print("IMPORT_MDB_ERROR: " + str(e))
    traceback.print_exc()
    sys.exit(1)

open_fn = None
try:
    from abaqus import openMdb
    open_fn = openMdb
except ImportError:
    open_fn = globals().get('openMdb', getattr(sys.modules.get('__main__'), 'openMdb', None))

if open_fn is None:
    print("OPEN_MDB_FN_NULL")
    sys.exit(1)

cae_path = "/tmp/ModeII_Geometry_Source_889c_recovered.cae"
print("Attempting openMdb on: " + cae_path)

try:
    open_fn(pathName=cae_path)
    print("OPEN_MDB_SUCCESS!")
    print("mdb.models keys: " + str(list(mdb.models.keys())))
    if 'ModeII_Geometry_Model' in mdb.models:
        m = mdb.models['ModeII_Geometry_Model']
        print("Model found. Parts: " + str(list(m.parts.keys())))
        print("Assembly instances: " + str(list(m.rootAssembly.instances.keys())))
        print("Steps: " + str(list(m.steps.keys())))
        print("RemeshingRules: " + str(list(m.remeshingRules.keys())))
        print("ALL_INVENTORY_CHECKS_PASS")
    else:
        print("MODEL_NAME_NOT_FOUND")
except Exception as e:
    print("OPEN_MDB_FAILED_WITH_EXCEPTION: " + str(e))
    traceback.print_exc()
    sys.exit(1)
