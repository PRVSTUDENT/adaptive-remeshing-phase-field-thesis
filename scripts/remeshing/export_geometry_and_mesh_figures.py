# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os

from abaqus import *
from abaqusConstants import *
import visualization
import odbAccess

def export_figures(odb_path, out_dir="."):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    session.graphicsOptions.setValues(backgroundColor='#FFFFFF', backgroundStyle=SOLID)
    vp = session.viewports['Viewport: 1']
    vp.makeCurrent()
    vp.viewportAnnotationOptions.setValues(triad=ON, title=OFF, state=OFF, annotations=OFF)

    if os.path.exists(odb_path):
        o = odbAccess.openOdb(path=odb_path, readOnly=True)
        vp.setValues(displayedObject=o)
        step_name = o.steps.keys()[-1]
        step_obj = o.steps[step_name]
        frame = step_obj.frames[-1]

        print("Available field outputs in frame:")
        for k, v in frame.fieldOutputs.items():
            pos = v.locations[0].position if v.locations else None
            print("  %s: %s" % (k, pos))

        if 'MISESERI' in frame.fieldOutputs:
            v_obj = frame.fieldOutputs['MISESERI']
            pos_const = v_obj.locations[0].position
            vp.odbDisplay.setPrimaryVariable(
                variableLabel='MISESERI',
                outputPosition=pos_const
            )
            vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
            vp.odbDisplay.contourOptions.setValues(contourStyle=CONTINUOUS)
            vp.view.fitView()

            session.printOptions.setValues(vpDecorations=OFF)
            miseseri_png = os.path.join(out_dir, "fig1_miseseri_contour_preanalysis.png")
            session.printToFile(fileName=miseseri_png, format=PNG, canvasObjects=[vp])
            print("Exported: %s" % miseseri_png)
        o.close()

if __name__ == "__main__":
    odb_p = sys.argv[-2] if len(sys.argv) > 2 else "PK_HOLE_METHOD_A_PREANALYSIS.odb"
    out_d = sys.argv[-1] if len(sys.argv) > 1 else "."
    export_figures(odb_p, out_d)
