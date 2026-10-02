from abaqus import mdb, session
from abaqusConstants import OFF, ON, PNG

out_dir = r"D:\Master thesis\Adaptive remeshing\docs\supervisor_reports\1-09-2026\MA_AdaptiveRemeshing_Report_2026_revised_content_pack\figures\generated"
cases = (
    (r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\02_proposed_adaptive_refined\PK_MODE1_PROPOSED_PFM_PHYS.inp", "PK_ACCEPTED_PHYSICAL", "fig13_adaptive_71320_mesh_cae"),
    (r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\02_proposed_adaptive_refined\PK_PREANALYSIS_COARSE.inp", "PK_COARSE", "fig03a_coarse_mesh_cae"),
    (r"D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\reference_convergence\M2REF_H0\M2REF_H0.inp", "M2_H0", "fig10_modeii_h0_mesh_cae"),
)

vp = session.viewports[session.currentViewportName]
vp.viewportAnnotationOptions.setValues(title=OFF, state=OFF, legend=OFF, triad=OFF, compass=OFF)
session.printOptions.setValues(vpDecorations=OFF, reduceColors=False)

for input_path, model_name, output_name in cases:
    model = mdb.ModelFromInputFile(name=model_name, inputFileName=input_path)
    if model.parts.keys():
        displayed = model.parts[list(model.parts.keys())[0]]
        nodes = len(displayed.nodes)
        elements = len(displayed.elements)
        vp.setValues(displayedObject=displayed)
        vp.partDisplay.setValues(mesh=ON)
    else:
        displayed = model.rootAssembly
        nodes = 0
        elements = 0
        for instance in displayed.instances.values():
            nodes += len(instance.nodes)
            elements += len(instance.elements)
        vp.setValues(displayedObject=displayed)
        vp.assemblyDisplay.setValues(mesh=ON)
    print("MESH_COUNT %s nodes=%d elements=%d parts=%s instances=%s" %
          (model_name, nodes, elements, list(model.parts.keys()), list(model.rootAssembly.instances.keys())))
    vp.view.fitView()
    session.printToFile(fileName=out_dir + "\\" + output_name, format=PNG, canvasObjects=(vp,))
