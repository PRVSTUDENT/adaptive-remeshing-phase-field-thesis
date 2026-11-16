# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 09:03:10 2026
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
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1811_single_target.py', 
    __main__.__dict__)
#: ================================================================================
#: RUNNING CASE 5: PLATE WITH SEVEN HOLES (TABLE 6 PARITY) AT ERROR TARGET 5.68%
#: Output directory: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\260_f1811_error_target_calibration\case5
#: Job name:         PK_F1811_CASE_5
#: ================================================================================
#: Donor ODB verified: PK_F1726_SEVEN_HOLE_COARSE.odb (SHA: CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E)
#: The model "Model_MethodA_case_5" has been created.
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
#: Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\260_f1811_error_target_calibration\case5\PK_F1811_CASE_5_PHYS.inp
#:   [AUDIT] Elements: 15466 (Quads: 15141, Tris: 325, Quad %: 97.90%)
#:   [AUDIT] Min signed det(J): 3.92157e-07, Max AR: 2.374, Coarsening: 2.12x
#: Receipt written: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\260_f1811_error_target_calibration\case5\PK_F1811_CASE_5_RECEIPT.json
