#!/usr/bin/env python3
import sys, os
from odbAccess import openOdb

def main():
    odb_path = "M2STATE_FRACFIX_RESTART2R4.odb"
    if not os.path.exists(odb_path):
        print "ERROR: ODB file not found:", odb_path
        sys.exit(1)
    odb = openOdb(odb_path, readOnly=True)
    print "ODB_OPEN_SUCCESS:", odb_path
    print "STEPS:", odb.steps.keys()
    odb.close()

if __name__ == '__main__':
    main()
