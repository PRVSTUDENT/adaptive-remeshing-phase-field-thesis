# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 15:48:02 2026
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
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1821_genuine_minmax_single.py', 
    __main__.__dict__)
#: 
#: ================================================================================
#: TASK F1821 GENUINE MINIMUM_MAXIMUM SIZING: CASE_5 (Case 5: Square Plate with Seven Holes)
#:   Executing RemeshingRule with sizingMethod=MINIMUM_MAXIMUM
#:   max_solution_error_target = 1.0%, min_solution_error_target = 5.0%, mesh_bias = 7
#:   Output dir: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\265_f1821_genuine_minmax
#: ================================================================================
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
#:   Total Elements: 51598 (Quads: 50538 = 97.95%, Tris: 1060)
#:   Min det(J): 2.19e-07, Max AR: 2.65
#:   Gate 06 Coarsening: 1.65x (Gate: FAIL)
#:   Scientific Gate (SCIENTIFIC_GATE_INTER_HOLE): 99.99% (Gate: PASS)
#:   Width metrics (h <= l0/2): Total fine = 45354
#:     Within 2*l0: 2746 (6.05%)
#:     Within 3*l0: 4168 (9.19%)
#:     Within 5*l0: 7336 (16.17%)
print('RT script done')
#: RT script done
