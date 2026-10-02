from abaqus import session
from abaqusConstants import ALL, CONTOURS_ON_UNDEF, ELEMENT_NODAL, INTEGRATION_POINT, OFF, ON, PNG, UNDEFORMED
from visualization import openOdb

odb_path = r"D:\Master thesis\Adaptive remeshing\runs\molnar_one_element_unchanged\20260714_technical_gate_local\evidence\OneElement.odb"
out_dir = r"D:\Master thesis\Adaptive remeshing\docs\supervisor_reports\1-09-2026\MA_AdaptiveRemeshing_Report_2026_revised_content_pack\figures\generated"

odb = openOdb(path=odb_path, readOnly=True)
vp = session.viewports[session.currentViewportName]
vp.setValues(displayedObject=odb)
vp.viewportAnnotationOptions.setValues(title=OFF, state=ON, legend=ON, triad=OFF, compass=OFF)
vp.odbDisplay.commonOptions.setValues(visibleEdges=ALL)
vp.odbDisplay.display.setValues(plotState=(UNDEFORMED,))
vp.view.fitView()
session.printOptions.setValues(vpDecorations=ON, reduceColors=False)
session.printToFile(fileName=out_dir + r"\fig02a_molnar_one_element_mesh", format=PNG, canvasObjects=(vp,))

vp.odbDisplay.setFrame(step=0, frame=len(odb.steps["Static"].frames) - 1)
vp.odbDisplay.setPrimaryVariable(variableLabel="SDV15", outputPosition=INTEGRATION_POINT)
vp.odbDisplay.contourOptions.setValues(minAutoCompute=OFF, minValue=0.0, maxAutoCompute=OFF, maxValue=1.0)
vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_UNDEF,))
vp.view.fitView()
session.printToFile(fileName=out_dir + r"\fig02a_molnar_one_element_sdv15", format=PNG, canvasObjects=(vp,))

odb.close()
