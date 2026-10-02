from odbAccess import openOdb

for path in (
    r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\01_standard_pfm_reference\PK_MODE1_STANDARD_PFM.odb",
    r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\02_proposed_adaptive_refined\PK_MODE1_PROPOSED_PFM.odb",
):
    odb = openOdb(path=path, readOnly=True)
    print("ODB", path)
    print("INSTANCES", list(odb.rootAssembly.instances.keys()))
    print("ASSEMBLY ELEMENT SETS", list(odb.rootAssembly.elementSets.keys()))
    for name, inst in odb.rootAssembly.instances.items():
        print("INSTANCE", name, "ELEMENTS", len(inst.elements), "SETS", list(inst.elementSets.keys()))
        counts = {}
        for elem in inst.elements:
            counts[elem.type] = counts.get(elem.type, 0) + 1
        print("TYPES", counts)
    odb.close()
