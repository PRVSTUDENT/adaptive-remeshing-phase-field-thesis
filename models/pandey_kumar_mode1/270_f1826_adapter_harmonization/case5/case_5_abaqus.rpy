# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Tue Nov 17 00:01:54 2026
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
execfile('scripts/remeshing/run_f1826_single_target.py', __main__.__dict__)
#: --- [F1826 Single] Case: case_5 | Target: 5.68% ---
#:   Donor ODB SHA-256: CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E
#: The model "Model_F1826_CASE_5" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       11
#: Number of Node Sets:          6
#: Number of Steps:              2
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       11
#: Number of Node Sets:          6
#: Number of Steps:              2
#:   Generated INP: models/pandey_kumar_mode1/270_f1826_adapter_harmonization/case5/PK_F1826_CASE_5_ADAPT_PHYS.inp
#:   INP Whole SHA: 54341CFE9AA87E420AFD02D4F8CC8D7461228380DEEA3E9C91992F15C00EA20C
#:   INP Body  SHA: 78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065
