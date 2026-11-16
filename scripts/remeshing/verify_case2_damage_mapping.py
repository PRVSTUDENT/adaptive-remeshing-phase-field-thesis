# -*- coding: utf-8 -*-
"""
verify_case2_damage_mapping.py
Verify the mapping between visualization element labels (5813 to 8718)
and physical elements (1 to 2906).
"""
from odbAccess import openOdb

odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
odb = openOdb(odb_path, readOnly=True)
inst = odb.rootAssembly.instances.values()[0]

elem_by_label = {e.label: e for e in inst.elements}

for i in [1, 50, 100, 500, 1000, 2000, 2906]:
    e_phys = elem_by_label[i]
    e_vis = elem_by_label[5812 + i]
    print("Phys %4d (type %s) conn: %s" % (e_phys.label, e_phys.type, e_phys.connectivity))
    print("Vis  %4d (type %s) conn: %s" % (e_vis.label, e_vis.type, e_vis.connectivity))
    assert e_phys.connectivity == e_vis.connectivity, "Connectivity mismatch for element %d" % i

print("ALL TESTED CONNECTIVITIES MATCH IDENTICALLY!")
odb.close()
