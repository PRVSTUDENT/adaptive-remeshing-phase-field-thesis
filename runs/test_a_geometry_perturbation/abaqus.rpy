# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Sun Nov 15 19:02:33 2026
#

# from driverUtils import executeOnCaeGraphicsStartup
# executeOnCaeGraphicsStartup()
#: Executing "onCaeGraphicsStartup()" in the site directory ...
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(1.36133, 1.36458), width=200.387, 
    height=135.367)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile(
    'D:/Master thesis/Adaptive remeshing/runs/test_a_geometry_perturbation/run_test_a_cae.py', 
    __main__.__dict__)
#: The model "Model-TestA" has been created.
#: Area of face = 8409.4159868246
#: TEST_A_CAD_FACE_AREA: 8409.4159868246
print('RT script done')
#: RT script done
