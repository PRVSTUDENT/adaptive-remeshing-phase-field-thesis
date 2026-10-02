#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract comprehensive nodal displacements, coordinates, and reaction forces
from M2STATE_FRACFIX_RESTART2R12_STEP1.odb using Abaqus Python.
"""
import sys
import json
from odbAccess import openOdb

def extract_r2r12_data(odb_path, output_json_path):
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    
    step_names = list(odb.steps.keys())
    print("Steps in ODB: %s" % step_names)
    last_step_name = step_names[-1]
    step = odb.steps[last_step_name]
    
    last_frame = step.frames[-1]
    print("Extracting from Step '%s', Frame %d, time = %f" % (last_step_name, last_frame.frameId, last_frame.frameValue))
    
    assembly = odb.rootAssembly
    instance = list(assembly.instances.values())[0] if assembly.instances else None
    
    # Extract node coordinates
    nodes_dict = {}
    if instance:
        for node in instance.nodes:
            nid = node.label
            nodes_dict[nid] = {
                'x': float(node.coordinates[0]),
                'y': float(node.coordinates[1]),
                'z': float(node.coordinates[2]) if len(node.coordinates) > 2 else 0.0,
                'u1': 0.0,
                'u2': 0.0,
                'u3': 0.0,
                'rf1': 0.0,
                'rf2': 0.0,
                'rf3': 0.0
            }
    else:
        for node in assembly.nodes:
            nid = node.label
            nodes_dict[nid] = {
                'x': float(node.coordinates[0]),
                'y': float(node.coordinates[1]),
                'z': float(node.coordinates[2]) if len(node.coordinates) > 2 else 0.0,
                'u1': 0.0,
                'u2': 0.0,
                'u3': 0.0,
                'rf1': 0.0,
                'rf2': 0.0,
                'rf3': 0.0
            }
            
    # Extract U field
    if 'U' in last_frame.fieldOutputs:
        u_field = last_frame.fieldOutputs['U']
        for val in u_field.values:
            nid = val.nodeLabel
            if nid in nodes_dict:
                data = val.data
                nodes_dict[nid]['u1'] = float(data[0]) if len(data) > 0 else 0.0
                nodes_dict[nid]['u2'] = float(data[1]) if len(data) > 1 else 0.0
                nodes_dict[nid]['u3'] = float(data[2]) if len(data) > 2 else 0.0

    # Extract RF field
    if 'RF' in last_frame.fieldOutputs:
        rf_field = last_frame.fieldOutputs['RF']
        for val in rf_field.values:
            nid = val.nodeLabel
            if nid in nodes_dict:
                data = val.data
                nodes_dict[nid]['rf1'] = float(data[0]) if len(data) > 0 else 0.0
                nodes_dict[nid]['rf2'] = float(data[1]) if len(data) > 1 else 0.0
                nodes_dict[nid]['rf3'] = float(data[2]) if len(data) > 2 else 0.0

    # Extract Node Sets
    node_sets = {}
    sets_source = instance.nodeSets if instance else assembly.nodeSets
    for sname, nset in sets_source.items():
        node_sets[sname] = [n.label for n in nset.nodes]

    # Extract Elements
    elements_dict = {}
    elems_source = instance.elements if instance else assembly.elements
    for elem in elems_source:
        eid = elem.label
        elements_dict[eid] = {
            'type': elem.type,
            'connectivity': [int(n) for n in elem.connectivity]
        }

    # Extract SDV if available
    sdv_dict = {}
    for key in last_frame.fieldOutputs.keys():
        if 'SDV' in key:
            sdv_dict[key] = {}
            for val in last_frame.fieldOutputs[key].values:
                eid = val.elementLabel
                ip = val.integrationPoint
                if eid not in sdv_dict[key]:
                    sdv_dict[key][eid] = {}
                sdv_dict[key][eid][ip] = float(val.data)

    out_data = {
        'candidate': 'M2STATE_FRACFIX_RESTART2R12',
        'step_name': last_step_name,
        'frame_id': last_frame.frameId,
        'frame_value': float(last_frame.frameValue),
        'node_count': len(nodes_dict),
        'element_count': len(elements_dict),
        'nodes': nodes_dict,
        'node_sets': node_sets,
        'elements': elements_dict,
        'sdv_fields': sdv_dict
    }

    with open(output_json_path, 'w') as f:
        json.dump(out_data, f)
        
    print("Successfully saved data for %d nodes and %d elements to %s" % (len(nodes_dict), len(elements_dict), output_json_path))
    odb.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: abaqus python extract_r2r12_step1_odb_data.py <odb_path> <output_json_path>")
        sys.exit(1)
    extract_r2r12_data(sys.argv[1], sys.argv[2])
