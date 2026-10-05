import sys, os
from odbAccess import openOdb

def extract_results():
    odb_path = "M2STATE_FRACFIX_RESTART2R5.odb"
    if not os.path.exists(odb_path):
        print "ODB not found:", odb_path
        sys.exit(1)
    odb = openOdb(odb_path, readOnly=True)
    print "ODB Opened successfully. Steps:", odb.steps.keys()
    odb.close()

if __name__ == '__main__':
    extract_results()
