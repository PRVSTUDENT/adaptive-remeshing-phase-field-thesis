#!/usr/bin/env python3
import os
import json
import sys

def main():
    audits = [
        'SOURCE_MODEL_INVENTORY.json',
        'INSTANCE_REPLACEMENT_API_AUDIT.json',
        'MODEL_ENTITY_REBINDING_AUDIT.json',
        'SLIT_GEOMETRY_AUDIT.json',
        'SLIT_MESH_TOPOLOGY_AUDIT.json',
        'GEOMETRY_BACKED_MODEL_AUDIT.json',
        'GENERATED_INPUT_AUDIT.json'
    ]
    
    for a_file in audits:
        if not os.path.exists(a_file):
            print('AUDIT PARSE ERROR: Missing audit file: %s' % a_file)
            return 1
            
    try:
        with open('GEOMETRY_BACKED_MODEL_AUDIT.json', 'r') as h:
            g_audit = json.load(h)
        with open('MODEL_ENTITY_REBINDING_AUDIT.json', 'r') as h:
            r_audit = json.load(h)
        with open('SLIT_GEOMETRY_AUDIT.json', 'r') as h:
            sg_audit = json.load(h)
        with open('SLIT_MESH_TOPOLOGY_AUDIT.json', 'r') as h:
            sm_audit = json.load(h)
    except Exception as e:
        print('AUDIT PARSE ERROR: Failed to parse JSON: %s' % str(e))
        return 1

    req_fields = {
        'contract_pass': True,
        'abaqus_cae_execution': True,
        'documented_remeshing_rule_signature': True,
        'documented_instance_replacement_api': True,
        'final_geometry_instance_name': 'Part-1-1',
        'final_geometry_instance_part': 'Part-1-GEOM',
        'model_entity_rebinding_pass': True,
        'unresolved_entity_count': 0,
        'stale_orphan_reference_count': 0,
        'output_region_mismatch_count': 0,
        'crack_face_identity_failure_count': 0,
        'input_written_by_job_writeInput': True
    }

    for k, v in req_fields.items():
        if g_audit.get(k) != v:
            print('AUDIT PARSE ERROR: key %s expected %s, got %s' % (k, v, g_audit.get(k)))
            return 1

    if r_audit.get('unresolved_entity_count') != 0 or r_audit.get('stale_orphan_reference_count') != 0 or r_audit.get('output_region_mismatch_count') != 0 or r_audit.get('crack_face_identity_failure_count') != 0:
        print('AUDIT PARSE ERROR: Rebinding audit failed counts')
        return 1

    if sg_audit.get('distinct_geometry_edge_ids') is not True or sg_audit.get('distinct_part_set_names') is not True:
        print('AUDIT PARSE ERROR: Slit geometry audit failed')
        return 1

    if sm_audit.get('disjoint_mesh_node_sets') is not True or sm_audit.get('bridge_element_count') != 0:
        print('AUDIT PARSE ERROR: Slit mesh topology audit failed')
        return 1

    print('F29 runtime audits successfully validated.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
