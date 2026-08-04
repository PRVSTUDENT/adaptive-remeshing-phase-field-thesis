# Python 2 and 3 compatible aggregate runtime audit validator for F30
# Imports os explicitly and validates all generated runtime JSON audit artifacts.
from __future__ import print_function
import sys
import os
import json

def load_json(path):
    if not os.path.exists(path):
        print("ERROR: Required runtime audit file missing: " + str(path))
        sys.exit(1)
    with open(path, 'r') as f:
        return json.load(f)

def main():
    # 1. Load all required audit files
    source_inv = load_json('SOURCE_MODEL_INVENTORY.json')
    inst_audit = load_json('INSTANCE_REPLACEMENT_API_AUDIT.json')
    rebind_audit = load_json('MODEL_ENTITY_REBINDING_AUDIT.json')
    slit_geom = load_json('SLIT_GEOMETRY_AUDIT.json')
    slit_mesh = load_json('SLIT_MESH_TOPOLOGY_AUDIT.json')
    geom_model = load_json('GEOMETRY_BACKED_MODEL_AUDIT.json')
    gen_inp = load_json('GENERATED_INPUT_AUDIT.json')

    failures = []

    # 2. Check INSTANCE_REPLACEMENT_API_AUDIT
    if not inst_audit.get('api_audit_pass', False):
        failures.append("INSTANCE_REPLACEMENT_API_AUDIT failed")

    # 3. Check MODEL_ENTITY_REBINDING_AUDIT
    if not rebind_audit.get('model_entity_rebinding_pass', False):
        failures.append("MODEL_ENTITY_REBINDING_AUDIT failed")
    if rebind_audit.get('unresolved_entity_count', -1) != 0:
        failures.append("Unresolved entity count is non-zero")
    if rebind_audit.get('source_contract_coverage', 0.0) != 1.0:
        failures.append("Source contract coverage is not 1.0")

    # 4. Check SLIT_GEOMETRY_AUDIT
    if not slit_geom.get('distinct_geometry_edge_ids', False):
        failures.append("SLIT_GEOMETRY_AUDIT distinct_geometry_edge_ids failed")
    if slit_geom.get('lower_edge_count', 0) == 0 or slit_geom.get('upper_edge_count', 0) == 0:
        failures.append("Lower or upper edge count is zero")

    # 5. Check SLIT_MESH_TOPOLOGY_AUDIT
    if not slit_mesh.get('open_slit_topology_preserved', False):
        failures.append("SLIT_MESH_TOPOLOGY_AUDIT open_slit_topology_preserved failed")
    if slit_mesh.get('bridge_element_count', -1) != 0:
        failures.append("Bridge element count is non-zero")

    # 6. Check GEOMETRY_BACKED_MODEL_AUDIT
    if not geom_model.get('contract_pass', False):
        failures.append("GEOMETRY_BACKED_MODEL_AUDIT contract_pass failed")

    # 7. Check GENERATED_INPUT_AUDIT
    if not gen_inp.get('exact_generated_input_contract_pass', False):
        failures.append("GENERATED_INPUT_AUDIT exact_generated_input_contract_pass failed")

    if len(failures) == 0:
        print("SUCCESS: All F30 runtime audits passed.")
        sys.exit(0)
    else:
        print("ERROR: F30 runtime audit validation failed:")
        for fail in failures:
            print("  - " + str(fail))
        sys.exit(1)

if __name__ == '__main__':
    main()
