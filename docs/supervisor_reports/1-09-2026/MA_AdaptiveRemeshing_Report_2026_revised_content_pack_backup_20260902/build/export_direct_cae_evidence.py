from abaqus import session
from abaqusConstants import ALL, CONTOURS_ON_UNDEF, INTEGRATION_POINT, OFF, ON, PNG, UNDEFORMED
from visualization import openOdb

out_dir = r"D:\Master thesis\Adaptive remeshing\docs\supervisor_reports\1-09-2026\MA_AdaptiveRemeshing_Report_2026_revised_content_pack\figures\generated"
molnar_odb = r"D:\Master thesis\Adaptive remeshing\runs\molnar_single_notch_author_supplied_exact\20260720_abaqus_cae_reproduction\work\Molnar_Author_SingleNotch_Exact.odb"

vp = session.viewports[session.currentViewportName]
vp.viewportAnnotationOptions.setValues(title=OFF, state=ON, legend=ON, triad=OFF, compass=OFF)
session.printOptions.setValues(vpDecorations=ON, reduceColors=False)

odb = openOdb(path=molnar_odb, readOnly=True)
vp.setValues(displayedObject=odb)
vp.odbDisplay.commonOptions.setValues(visibleEdges=ALL)
states = (
    ("Step-1", 20, "fig02c_cae_molnar_u0020"),
    ("Step-1", 50, "fig02c_cae_molnar_u0050"),
    ("Step-2", 10, "fig02c_cae_molnar_u0060"),
    ("Step-2", 20, "fig02c_cae_molnar_u0070"),
)
for step_name, frame_id, output_name in states:
    step_index = list(odb.steps.keys()).index(step_name)
    vp.odbDisplay.setFrame(step=step_index, frame=frame_id)
    vp.odbDisplay.setPrimaryVariable(variableLabel="SDV15", outputPosition=INTEGRATION_POINT)
    vp.odbDisplay.contourOptions.setValues(minAutoCompute=OFF, minValue=0.0, maxAutoCompute=OFF, maxValue=1.0)
    vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_UNDEF,))
    vp.view.fitView()
    session.printToFile(fileName=out_dir + "\\" + output_name, format=PNG, canvasObjects=(vp,))
odb.close()

mesh_cases = (
    (r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\01_standard_pfm_reference\PK_MODE1_STANDARD_PFM.odb", "fig13_standard_mode1_mesh_cae"),
    (r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\02_proposed_adaptive_refined\PK_MODE1_PROPOSED_PFM.odb", "fig13_adaptive_71320_mesh_cae"),
)
for mesh_odb_path, output_name in mesh_cases:
    mesh_odb = openOdb(path=mesh_odb_path, readOnly=True)
    vp.setValues(displayedObject=mesh_odb)
    vp.odbDisplay.commonOptions.setValues(visibleEdges=ALL)
    vp.odbDisplay.display.setValues(plotState=(UNDEFORMED,))
    vp.view.fitView()
    session.printToFile(fileName=out_dir + "\\" + output_name, format=PNG, canvasObjects=(vp,))
    mesh_odb.close()
