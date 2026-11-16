# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 09:03:02 2026
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
#: RUNNING CASE 1: MODE-I EDGE-CRACKED PLATE AT ERROR TARGET 1.85%
#: Output directory: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\260_f1811_error_target_calibration\case1
#: Job name:         PK_F1811_CASE_1
#: ================================================================================
#: Donor ODB verified: PK_F1807_CASE1_COARSE_DONOR.odb (SHA: DF246BEA9AD9AD5DD650073156322C6C2213B1B3A26C2C66ECE11D1691E9DCF0)
#: The model "Model_MethodA_case_1" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/257_f1807_four_case_regression/case1/PK_F1807_CASE1_COARSE_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/257_f1807_four_case_regression/case1/PK_F1807_CASE1_COARSE_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\260_f1811_error_target_calibration\case1\PK_F1811_CASE_1_PHYS.inp
#:   [AUDIT] Elements: 14087 (Quads: 13667, Tris: 420, Quad %: 97.02%)
#:   [AUDIT] Min signed det(J): 2.47887e-07, Max AR: 2.640, Coarsening: 2.54x
#: Receipt written: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\260_f1811_error_target_calibration\case1\PK_F1811_CASE_1_RECEIPT.json
