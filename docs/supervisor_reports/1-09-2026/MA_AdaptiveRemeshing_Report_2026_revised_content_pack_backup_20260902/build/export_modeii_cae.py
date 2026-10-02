from abaqus import session
from abaqusConstants import ALL, CONTOURS_ON_UNDEF, INTEGRATION_POINT, NONE, OFF, ON, PNG, UNDEFORMED
from visualization import openOdb

out_dir = r"D:\Master thesis\Adaptive remeshing\docs\supervisor_reports\1-09-2026\MA_AdaptiveRemeshing_Report_2026_revised_content_pack\figures\generated"
cases = (
    (r"D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\reference_convergence\M2REF_H1\M2REF_H1.odb", "h1"),
    (r"D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\reference_convergence\M2REF_H2\M2REF_H2.odb", "h2"),
)
vp = session.viewports[session.currentViewportName]
vp.viewportAnnotationOptions.setValues(title=OFF, state=OFF, legend=OFF, triad=OFF, compass=OFF)
session.printOptions.setValues(vpDecorations=OFF, reduceColors=False)

for path, tag in cases:
    odb = openOdb(path=path, readOnly=True)
    vp.setValues(displayedObject=odb)
    vp.odbDisplay.commonOptions.setValues(visibleEdges=ALL)
    vp.odbDisplay.display.setValues(plotState=(UNDEFORMED,))
    vp.view.fitView()
    session.printToFile(fileName=out_dir + "\\fig10_modeii_%s_mesh_cae" % tag, format=PNG, canvasObjects=(vp,))

    vp.viewportAnnotationOptions.setValues(legend=ON)
    vp.odbDisplay.setFrame(step=1, frame=20)
    vp.odbDisplay.setPrimaryVariable(variableLabel="SDV14", outputPosition=INTEGRATION_POINT)
    vp.odbDisplay.contourOptions.setValues(minAutoCompute=OFF, minValue=0.0, maxAutoCompute=OFF, maxValue=1.0)
    vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_UNDEF,))
    vp.odbDisplay.commonOptions.setValues(visibleEdges=NONE)
    vp.view.fitView()
    session.printToFile(fileName=out_dir + "\\fig10_modeii_%s_phase_cae" % tag, format=PNG, canvasObjects=(vp,))
    vp.viewportAnnotationOptions.setValues(legend=OFF)
    odb.close()
